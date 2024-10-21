from flask import Flask, request, jsonify, render_template, session as flask_session, send_from_directory, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)

# Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'

# Database initialization
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    balance = db.Column(db.Float, default=0)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='user1').first():
            user1 = User(username='user1')
            user1.set_password('password1')
            user1.balance = 100000000000
            db.session.add(user1)
            db.session.commit()

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if User.query.filter_by(username=username).first():
        return 'User already exists', 400

    new_user = User(username=username)
    new_user.set_password(password)
    db.session.add(new_user)
    db.session.commit()

    return 'User created successfully', 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        flask_session['logged_in_user'] = user.id
        balance = user.balance

        return jsonify({'balance': balance}), 200
    else:
        return 'Login failed', 401

@app.route('/api/deposit', methods=['POST'])
def deposit():
    if 'logged_in_user' not in flask_session:
        return 'Not logged in', 401

    data = request.get_json()
    to_account_username = data.get('toAccount')
    amount = float(data.get('amount'))

    from_user = User.query.get(flask_session['logged_in_user'])
    to_user = User.query.filter_by(username=to_account_username).first()

    # Allow deposit only to the specific account
    if to_account_username != '1976278463':
        return 'Deposits can only be made to account 1976278463', 400

    if from_user.balance >= amount and amount > 0:
        from_user.balance -= amount
        if not to_user:
            to_user = User(username=to_account_username)
            db.session.add(to_user)
        to_user.balance += amount
        db.session.commit()
        balance = from_user.balance
        return jsonify({'balance': balance}), 200
    else:
        return 'Insufficient balance or invalid amount', 400

@app.route('/<path:path>')
def serve_static_files(path):
    return send_from_directory('public', path)

# Initialize the database
init_db()

if __name__ == '__main__':
    app.run(port=3000)





