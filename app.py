from flask import Flask
from backend.models import db, Admin

app = None
def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///parking_data.db'
    app.config['SECRET_KEY'] = 'anjali_123'

    db.init_app(app)
    app.app_context().push()
    app.debug = True
    print("App created successfully.")

create_app()

from backend.controller import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        admin = Admin.query.filter_by(email='anjalirkokare@gmail.com').first()
        if not admin:
            admin = Admin(
                email='anjalirkokare@gmail.com',
                password= '123456'
            )
            db.session.add(admin)
            db.session.commit()

    app.run()