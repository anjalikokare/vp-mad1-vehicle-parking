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

@app.route('/admin/admin_all_bookings')
def all_bookings():
    if 'admin_id' not in session:
        flash("Only admin can access this page", "danger")
        return redirect('/admin_login')

    bookings = Reservation.query.order_by(Reservation.parking_timestamp.desc()).all()
    return render_template('admin_all_booking.html', bookings=bookings)





