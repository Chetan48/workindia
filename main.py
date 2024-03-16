
from flask import Flask, request, jsonify, g
from flask_sqlalchemy import SQLAlchemy
import uuid
from functools import wraps


app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:chetan@localhost/pets'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'user'

class Train(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    train_name = db.Column(db.String(100), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    seat_capacity = db.Column(db.Integer, nullable=False)
    arrival_time_at_source = db.Column(db.String(20), nullable=False)
    arrival_time_at_destination = db.Column(db.String(20), nullable=False)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    train_id = db.Column(db.Integer, nullable=False)
    no_of_seats = db.Column(db.Integer, nullable=False)
    seat_numbers = db.Column(db.String(100), nullable=False)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user.role != 'admin':
            return jsonify({"error": "Unauthorized access"}), 401
        return f(*args, **kwargs)
    return decorated_function



@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.json
    new_user = User(username=data['username'], password=data['password'], email=data['email'], role='user')
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"status": "Account successfully created", "status_code": 200, "user_id": new_user.id})


@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username'], password=data['password']).first()
    if user:
        access_token = str(uuid.uuid4())
        return jsonify({"status": "Login successful", "status_code": 200, "user_id": user.id, "access_token": access_token})
    else:
        return jsonify({"status": "Incorrect username/password provided. Please retry", "status_code": 401})


@app.route('/api/trains/create', methods=['POST'])
@admin_required
def create_train():
    data = request.json
    new_train = Train(train_name=data['train_name'], source=data['source'], destination=data['destination'],
                      seat_capacity=data['seat_capacity'], arrival_time_at_source=data['arrival_time_at_source'],
                      arrival_time_at_destination=data['arrival_time_at_destination'])
    db.session.add(new_train)
    db.session.commit()
    return jsonify({"message": "Train added successfully", "train_id": new_train.id})


@app.route('/api/trains/availability', methods=['GET'])
def get_seat_availability():
    data = request.json
    
    source = data["source"]
    
    destination = data["destination"]
    trains = Train.query.filter_by(source=source, destination=destination).all()
    print(trains)
    availability = [{"train_id": train.id, "train_name": train.train_name,
                     "available_seats": train.seat_capacity - Booking.query.filter_by(train_id=train.id).count()}
                    for train in trains]
    return jsonify(availability)



@app.route('/api/trains/<int:train_id>/book', methods=['POST'])
def book_seat(train_id):
    data = request.json
    
    
    train = Train.query.get(train_id)
    if not train:
        return jsonify({"error": "Train not found"}), 404

    
    if Booking.query.filter_by(train_id=train_id).count() >= train.seat_capacity:
        return jsonify({"error": "No seats available"}), 400
    
    


    booking = Booking(user_id=data['user_id'], train_id=train_id, no_of_seats=data['no_of_seats'], seat_numbers=1)
    db.session.add(booking)
    db.session.commit()
    
    return jsonify({"message": "Seat booked successfully", "booking_id": booking.id, "seat_numbers": booking.seat_numbers})


@app.route('/api/bookings/<int:booking_id>', methods=['GET'])
def get_booking_details(booking_id):
    booking = Booking.query.get(booking_id)
    if not booking:
        return jsonify({"error": "Booking not found"}), 404
    
    
    train = Train.query.get(booking.train_id)
    if not train:
        return jsonify({"error": "Train not found"}), 404
    
    return jsonify({
        "booking_id": booking.id,
        "train_id": train.id,
        "train_name": train.train_name,
        "user_id": booking.user_id,
        "no_of_seats": booking.no_of_seats,
        "seat_numbers": booking.seat_numbers,
        "arrival_time_at_source": train.arrival_time_at_source,
        "arrival_time_at_destination": train.arrival_time_at_destination
    })

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        app.run(debug=True)
