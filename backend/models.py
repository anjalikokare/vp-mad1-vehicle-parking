from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)  
    address = db.Column(db.String(200), nullable=True)
    pin_code = db.Column(db.String(20), nullable=True)
    reservations = db.relationship('Reservation', backref='user', lazy=True)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
   
    
class Parking_lot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    prime_location_name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=True)
    maximum_number_of_spots = db.Column(db.Integer, nullable=False)
    address = db.Column(db.String(200), nullable=True)
    pin_code = db.Column(db.String(20), nullable=True)
    city = db.Column(db.String(20), nullable=False)  
    spots = db.relationship('Parking_spot', backref='lot', lazy=True)

class Parking_spot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Available') 
    spot_name = db.Column(db.String(20))
    place = db.Column(db.String(20))
    city = db.Column(db.String(20))  
    reservations = db.relationship('Reservation', backref='spot', lazy=True)

class Reservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    parking_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    leaving_timestamp = db.Column(db.DateTime)
    parking_cost = db.Column(db.Float)
    vehicle_number = db.Column(db.String(50))
    city = db.Column(db.String(50))
    place = db.Column(db.String(50))
    lot_id = db.Column(db.Integer, db.ForeignKey('parking_lot.id'), nullable=False)
    lot = db.relationship('Parking_lot', backref='reservations')
   

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(50))
    city = db.Column(db.String(50))             
    place = db.Column(db.String(50))         
    spot_name = db.Column(db.String(10))   
    lot_id = db.Column(db.Integer)            
    user_id = db.Column(db.Integer)            
    vehicle_type = db.Column(db.String(20)) 
