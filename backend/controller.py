from flask import Flask, render_template, request, redirect, flash, session , url_for
from datetime import datetime
from backend.models import *
from flask import current_app as app
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os



@app.route('/')
def home():
    return render_template('index.html')


@app.route('/select_city_place', methods=['POST'])
def select_city_place():
    city = request.form.get('city')
    place = request.form.get('place')
    session['selected_city'] = city
    session['selected_place'] = place
    return redirect('/booking')
  
    
@app.route('/booking', methods=['GET', 'POST'])
def booking():
    city = session.get('selected_city')
    place = session.get('selected_place')

    lot = Parking_lot.query.filter_by(city=city, prime_location_name=place).first()
    if not lot:
        flash("Parking lot not found.", "danger")
        return redirect('/')

    if request.method == 'POST':
        vehicle_number = request.form.get('number')
        user_id = session.get('user_id')
        spot = Parking_spot.query.filter_by(lot_id=lot.id, status='Available').order_by(Parking_spot.spot_name.asc()).first()

        if not spot:
            flash("No available spots.", "danger")
            return redirect('/booking')
        spot.status = 'Booked'
        db.session.add(spot)
        
        booking = Booking(
            vehicle_number=vehicle_number,
            city=city,
            place=place,
            spot_name=spot.spot_name,
            lot_id=lot.id,
            user_id=user_id
        )
        db.session.add(booking)

        reservation = Reservation(
            spot_id=spot.id,
            user_id=user_id,
            lot_id=lot.id,
            parking_timestamp=datetime.utcnow(),
            parking_cost=0.0,
            vehicle_number=vehicle_number,
            city=city,     
            place=place,
            spot_name=spot.spot_name
        )
        db.session.add(reservation)

        db.session.commit()
        flash("Your Park is Booked Successfully!", "success")
        return redirect('/user_dashboard')
    
    spot_list = Parking_spot.query.filter_by(lot_id=lot.id, status='Available').order_by(Parking_spot.spot_name.asc()).all()
    spot = spot_list[0] if spot_list else None
    spot_name = spot.spot_name if spot else "Not Available"

    return render_template(
        'info.html',
        lot=lot,
        spot_list=spot_list,
        spot_name=spot_name
    )


@app.route('/release_spot/<int:reservation_id>', methods=['POST'])
def release_spot(reservation_id):
    reservation = Reservation.query.get(reservation_id)
    if not reservation or reservation.user_id != session['user_id']:
        flash("Invalid operation", "danger")
        return redirect('/user_dashboard')

    spot = Parking_spot.query.get(reservation.spot_id)

    if spot:
        spot.status = 'Available'
        reservation.leaving_timestamp = datetime.utcnow()

        duration = reservation.leaving_timestamp - reservation.parking_timestamp
        hours = duration.total_seconds() / 3600
        reservation.parking_cost = hours * 100
        db.session.commit()
        flash("Spot released successfully.", "success")
    else:
        flash("Parking spot not found.", "danger")

    return redirect('/user_dashboard')


@app.route('/admin/dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin_id' in session:
        admin = Admin.query.get(session['admin_id']) 
        lots = Parking_lot.query.all()
        for lot in lots:
            lot.spots = Parking_spot.query.filter_by(lot_id=lot.id).all()
            lot.available = len([s for s in lot.spots if s.status == 'Available'])
            lot.total = len(lot.spots)
            lot.occupied = lot.total - lot.available
        return render_template('admin_dashboard.html',lots = lots, admin=admin)
    else:
        flash("Please login first", "danger")
        return redirect('/admin_login')

@app.route('/user_registration', methods = ['GET','POST'])
def user_registration():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        address = request.form.get('address')
        pincode = request.form.get('pincode')

        if not name or not email or not password or not address or not pincode:
            flash("Please fill out all fields", "danger")
            return redirect('/user_registration')

        user = User.query.filter_by(email = email).first()
        if user:
            flash("Email already exists", "danger")
            return redirect('/user_registration')
        
        new_user = User(
            name = name,
            address = address,
            pin_code = pincode,
            email = email,
            password = password,
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect('/user_login')
    return render_template('user_registration.html')



@app.route('/user_login', methods = ['GET','POST'])
def user_login():
    if 'user_id' in session:
        return redirect('/user_dashboard')
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash("Please fill out all fields", "danger")
            return redirect('/user_login')
        
        user = User.query.filter_by(email = email).first()
        if not user:
            flash("email does not exist.", "danger")
            return redirect('/user_login')
        
        if user.password != password:
            flash("Incorrect password", "danger")
            return redirect('/user_login')
        else:     
            session['user_id'] = user.id
            session['name'] = user.name
            flash("Login successful", "success")
    
        return redirect('/user_dashboard')
    return render_template('user_login.html')
    
@app.route('/admin_login', methods = ['GET','POST'])
def admin_login():
    if 'admin_id' in session:
        return redirect('/admin/dashboard')     
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if not email or not password:
            flash("Please fill out all fields", "danger")
            return redirect('/admin_login')
        
        admin = Admin.query.filter_by(email = email).first()
        if admin.password != password:
            flash("Incorrect password", "danger")
            return redirect('/admin_login')
        else:
            session['admin_id'] = admin.id
            flash("Login successful", "success")
        return redirect('/admin/dashboard')
    return render_template('admin_login.html')

@app.route('/create', methods=['GET', 'POST'])
def create_lot():
    if request.method == 'POST':

        place = request.form.get('place')
        city = request.form.get('city')
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        price = float(request.form.get('price'))
        max_spots = int(request.form.get('max_spots'))

        if not place or not city or not address or not pincode or not price or not max_spots:
            flash("Please fill out all fields", "danger")
            return redirect('/create')

        new_lot = Parking_lot(
            prime_location_name = place,
            address = address,
            pin_code = pincode,
            price = price,
            city = city,
            maximum_number_of_spots = max_spots
        )
        db.session.add(new_lot)
        db.session.commit()
        flash("New Parking Lot Created Successfully", "success")
        
        spot_names = [chr(i) for i in range(65, 65 + max_spots)]

        for i in range(max_spots):
            spot = Parking_spot(
                lot_id = new_lot.id,
                city = new_lot.city,
                place = new_lot.prime_location_name,
                spot_name = spot_names[i],
                status = 'Available'
            )
            db.session.add(spot)

        db.session.commit()
        flash("New Parking Lot Created", "success")
        return redirect('/create')

    return render_template('create.html')



@app.route('/edit/<int:lot_id>', methods=['GET', 'POST'])
def edit(lot_id):
    lot = Parking_lot.query.get(lot_id)
    if not lot:
        flash('Parking lot not found.', 'danger')
        return redirect('/')

    if request.method == 'POST':
        place = request.form.get('place')
        city = request.form.get('city')
        address = request.form.get('address')
        pincode = request.form.get('pincode')
        price = request.form.get('price')
        max_spots = request.form.get('max_spots')

        if not place or not city or not address or not pincode or not price or not max_spots:
            flash('Please fill out all fields.', 'danger')
            return redirect(url_for('edit', lot_id=lot_id))

        lot.prime_location_name = place
        lot.city = city
        lot.address = address
        lot.pin_code = pincode
        lot.price = price
        lot.maximum_number_of_spots = max_spots

        for spot in lot.spots:
            spot.city = city
            spot.place = place

        old_spots = Parking_spot.query.filter_by(lot_id=lot.id).all()
        old_count = len(old_spots)
        new_count = int(max_spots)

        used_names = [s.spot_name for s in old_spots]
        used_letter = 'A'
        max_letter = max(used_names)
        

        if new_count > old_count:
            for i in range(new_count - old_count):
                next_letter = chr(ord(max_letter) + 1 + i)
                new_spot = Parking_spot(
                    lot_id=lot.id,
                    spot_name=next_letter,
                    status='Available'
                )
                db.session.add(new_spot)


        elif new_count < old_count:
            extra = old_count - new_count
            for_removing = [s for s in old_spots if s.status == 'Available']
            if len(for_removing) < extra:
                flash('Not enough available spots to remove.', 'danger')
            else:
                for spot in for_removing[extra:]:
                    db.session.delete(spot)
        db.session.commit()
        flash('Parking lot updated successfully.', 'success')
        return redirect('/admin/dashboard')

    return render_template('edit.html', lot=lot)

@app.route('/delete_lot/<int:lot_id>', methods=['POST'])
def delete_lot(lot_id):
    if 'admin_id' not in session:
        flash("Only admin can delete lots.", "danger")
        return redirect('/admin_login')

    lot = Parking_lot.query.get(lot_id)
    if not lot:
        flash("Parking lot not found", "danger")
        return redirect('/admin/dashboard')

    booked_spot = Parking_spot.query.filter_by(lot_id=lot.id, status='Booked').first()
    if booked_spot:
        flash("Cannot delete. Some spots are still booked in this lot.", "warning")
        return redirect('/admin/dashboard')

    spots = lot.spots
    for spot in spots:
        db.session.delete(spot)
    db.session.delete(lot)
    db.session.commit()
    flash("Parking lot deleted successfully.", "success")
    return redirect('/admin/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/admin/admin_all_bookings')
def all_bookings():
    if 'admin_id' not in session:
        flash("Only admin can access this page", "danger")
        return redirect('/admin_login')

    bookings = Reservation.query.order_by(Reservation.parking_timestamp.desc()).all()
    return render_template('admin_all_booking.html', bookings=bookings)


@app.route('/admin/view_spots/<int:lot_id>', methods=['GET', 'POST'])
def view_spots(lot_id):
    if 'admin_id' not in session:
        flash("Only admin can access this page", "danger")
        return redirect('/admin_login')

    lot = Parking_lot.query.get(lot_id)
    if not lot:
        flash("Parking lot not found", "danger")
        return redirect('/admin/dashboard')

    spots = Parking_spot.query.filter_by(lot_id=lot.id).all()
    return render_template('view_spots.html', spots=spots, lot=lot)


# i want to create view spot details page
@app.route('/admin/view_spot_details/<int:spot_id>', methods=['GET', 'POST'])
def view_spot_details(spot_id):
    if 'admin_id' not in session:
        flash("Only admin can access this page", "danger")
        return redirect('/admin_login')

    spot = Parking_spot.query.get(spot_id)
    if not spot:
        flash("Spot not found", "danger")
        return redirect('/admin/dashboard')
    reservation = Reservation.query.filter_by(spot_id=spot_id).order_by(Reservation.id.desc()).first()

    return render_template('view_spot_details.html', selected_spot=spot, reservation=reservation)

# i want to add a user all details showing page to admin can view
@app.route('/admin/user', methods=['GET', 'POST'])
def user():
    if 'admin_id' not in session:
        flash("Only admin can access this page", "danger")
        return redirect('/admin_login')

    users = User.query.all()
    return render_template('user.html', users=users)


@app.route('/user_dashboard', methods=['GET', 'POST'])
def user_dashboard(): 
    if 'user_id' not in session:
        flash("Please log in first", "danger")
        return redirect('/user_login')

    user = User.query.get(session['user_id'])

    if not user:
        flash("User not found. Please log in again.", "danger")
        session.pop('user_id', None)
        return redirect('/user_login')
    
    reservations = Reservation.query.filter_by(user_id=user.id).order_by(Reservation.parking_timestamp.desc()).all()
    lots = Parking_lot.query.all()
    for lot in lots:
        available_spots = Parking_spot.query.filter_by(lot_id=lot.id, status='Available').count()
        lot.available_spots = available_spots

    return render_template("user_dashboard.html", 
                        user = user,
                        reservations=reservations, 
                        lots=lots)

    
@app.route('/release_form/<int:reservation_id>', methods=['GET', 'POST'])
def release_form(reservation_id):
    reservation = Reservation.query.get(reservation_id)
    return render_template('release_form.html', reservation=reservation)

# i want to create a summary page route for user side
@app.route('/admin/summary', methods=['GET', 'POST'])
def admin_summary():
    lots = Parking_lot.query.all()

    lot_names = []
    revenue = []
    for lot in lots:
        lot_names.append(lot.prime_location_name)
        reservations = Reservation.query.filter_by(lot_id=lot.id).all()
        total_revenue = 0
        for res in reservations:
            if res.parking_cost:
                total_revenue  += res.parking_cost
        revenue.append(total_revenue)
    
   
    plt.bar(lot_names, revenue,color='seagreen')
    plt.xlabel('Parking Lots', fontsize=15)
    plt.ylabel('Revenue', fontsize=15)
    plt.title('Revenue For Each Parking Lot', fontsize=20)
    plt.savefig('static/revenue_chart.png')
    plt.close()

    available_count = []
    booked_count = []

    for lot in lots:
        available = Parking_spot.query.filter_by(lot_id=lot.id, status='Available').count()
        available_count.append(available)
        booked = Parking_spot.query.filter_by(lot_id=lot.id, status='Booked').count()
        booked_count.append(booked)

    plt.bar(lot_names, available_count, color='seagreen')
    plt.xlabel('Parking Lots', fontsize=15)
    plt.ylabel('Available Spots', fontsize=15)
    plt.title('Available Spots For Each Parking Lot', fontsize=20)
    plt.savefig('static/available_chart.png')
    plt.close()

    plt.bar(lot_names, booked_count, color='seagreen')
    plt.xlabel('Parking Lots', fontsize=15)
    plt.ylabel('Booked Spots', fontsize=15)
    plt.title('Booked Spots For Each Parking Lot', fontsize=20)
    plt.savefig('static/booked_chart.png')
    plt.close()
    return render_template('admin_summary.html',lots=lots, lot_names=lot_names, revenue=revenue
                           ,available_count=available_count,booked_count=booked_count)


@app.route('/user/summary', methods=['GET', 'POST'])
def user_summary():
    lots = Parking_lot.query.all()

    lot_names = []
    already_used_spots = []
    for lot in lots:
        lot_names.append(lot.prime_location_name)
        used_spots_count = Reservation.query.filter_by(lot_id=lot.id).count()
        already_used_spots.append(used_spots_count)
        if lot_names and already_used_spots and len(lot_names) == len(already_used_spots):
            plt.bar(lot_names, already_used_spots,color='seagreen')
            plt.xlabel('Parking Lots', fontsize=15)
            plt.ylabel('already used spots', fontsize=15)
            plt.title('Summary on Already Used Parking Spots', fontsize=20)
            plt.savefig('static/used_spots_chart.png')
            plt.close()
    return render_template('user_summary.html',lots=lots, lot_names=lot_names,
    already_used_spots=already_used_spots)
