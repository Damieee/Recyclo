from flask import request, jsonify, abort
from models import db, User, TokenBlacklist
from authentication.email_authentication import EmailAuthentication
from geopy.distance import geodesic
from GPS_Tracking.recycle_bin_locations import bins, Gps
from reward.recycle_reward import reward_cards
from flask import Flask



# Initialize the Flask application
app = Flask(__name__)

# Configure the Flask app to use a SQLite database using Flask SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
gps=Gps()

# Define the routes for the Flask app

# Define the routes for the Flask app
@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'Welcome My Friend'}), 201

@app.route('/signup/<username>/<email>/<password>', methods=['GET', 'POST'])
def register(username, email, password):
    db.create_all()

    email_authentication=EmailAuthentication(username=username, email=email)

    if not username or not email or not password:
        return jsonify({'message': 'Please enter all required information.'}), 400

    if not email_authentication.validate_email_payload():
        return jsonify({'message': 'Please enter a valid username and email'}), 400


    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return jsonify({'message': 'That username or email already exists. Please choose another.'}), 400

    user = User(username=username, email=email)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({'message': f'User {username} successfully registered.'}), 201

@app.route('/signin/<string:username_or_email>/<password>', methods=['GET', 'POST'])
def login(username_or_email, password):
    if not username_or_email or not password:
        return jsonify({'message': 'Please enter your username or email and password.'}), 400

    user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()

    if not user or not user.check_password(password):
        return jsonify({'message': 'Invalid login credentials. Please try again.'}), 401

    auth_token = user.encode_auth_token(user.id)
    return jsonify({'message': f'Welcome back, {user.username}.'}), 200


@app.route('/forgot_password/<email>', methods=['GET','POST'])
def forgot_password(email):
    if not email:
        return jsonify({'message': 'Please enter your email.'}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({'message': 'Invalid email. Please try again.'}), 401

    reset_token = user.generate_password_reset_token(email)

    # Here you would send an email to the user containing the reset token
    # You could use a service like SendGrid or Mailgun to handle this

    return jsonify({'message': 'An email containing instructions to reset your password has been sent.'}), 200


@app.route('/change_password/<email>/<old_password>/<new_password>', methods=['GET', 'POST'])
def change_password(email, old_password, new_password):
    if not old_password or not new_password:
        return jsonify({'message': 'Please enter your old and new password.'}), 400

    user = User.query.filter((User.email == email)).first()

    if not user.check_password(old_password):
        return jsonify({'message': 'Invalid old password. Please try again.'}), 401

    user.set_password(new_password)
    db.session.commit()

    return jsonify({'message': 'Password successfully changed.'}), 200


@app.route('/gps')
def get_bins():
    location=gps.gps_location()
    user_lat = location["Latitude"]
    user_lon = location["Latitude"]

    bins_with_distance = [
        {
            'id': bin['id'],
            'name': bin['name'],
            'address': bin['address'],
            'distance': geodesic((user_lat, user_lon), (bin['lat'], bin['lon'])).km
        }
        for bin in bins
    ]
    bins_sorted_by_distance = sorted(bins_with_distance, key=lambda bin: bin['distance'])
    return jsonify({'bins': bins_sorted_by_distance})

@app.route('/rewards', methods=['GET'])
def get_rewards():
    return jsonify({'rewards': reward_cards})

@app.route('/rewards/<int:reward_id>', methods=['GET'])
def get_reward(reward_id):
    reward = [reward for reward in reward_cards if reward['id'] == reward_id]
    if len(reward) == 0:
        abort(404)
    return jsonify({'reward': reward[0]})


if __name__=="__main__":
    app.run(debug=True)
