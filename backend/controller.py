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





