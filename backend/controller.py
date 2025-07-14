from flask import Flask, render_template, request, redirect, flash, session , url_for
from datetime import datetime
from backend.models import *
from flask import current_app as app
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt



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
                for spot in for_removing[:extra]:
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

@app.route('/admin/delete_spot/<int:spot_id>', methods=['POST'])
def delete_spot(spot_id):
    if 'admin_id' not in session:
        flash("Only admin can see this page", "danger")
        return redirect('/admin_login')

    spot = Parking_spot.query.get(spot_id)
    if not spot:
        flash("Spot not found", "danger")
        return redirect('/admin/dashboard')

    if spot.status == 'Booked':
        flash("Cannot delete a booked spot", "warning")
        return redirect(url_for('view_spots', lot_id=spot.lot_id))
    
    lot = Parking_lot.query.get(spot.lot_id)
    lot.maximum_number_of_spots -= 1

    db.session.delete(spot)
    db.session.add(lot)
    db.session.commit()
    flash("Spot deleted successfully", "success")
    return redirect(url_for('view_spots', lot_id=spot.lot_id))

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


