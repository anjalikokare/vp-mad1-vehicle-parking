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
            vehicle_number=vehicle_number
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




