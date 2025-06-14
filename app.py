from flask import Flask, render_template, request, redirect, url_for, flash
import numpy as np
import joblib
import os
from config import config
import pandas as pd
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
    
    db = SQLAlchemy(app)

    # User model
    class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True, nullable=False)
        email = db.Column(db.String(120), unique=True, nullable=False)
        password_hash = db.Column(db.String(128))
        created_at = db.Column(db.DateTime, default=datetime.utcnow)

        def set_password(self, password):
            self.password_hash = generate_password_hash(password)

        def check_password(self, password):
            return check_password_hash(self.password_hash, password)

    # Create database tables
    with app.app_context():
        db.create_all()

    # Load the trained model
    try:
        model = joblib.load("model.pkl")
    except Exception as e:
        print(f"Error loading model: {e}")
        model = None

    @app.route('/')
    def home():
        return render_template("index.html")

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')

            # Validation
            if not all([username, email, password, confirm_password]):
                return render_template('signup.html', error='All fields are required')

            if password != confirm_password:
                return render_template('signup.html', error='Passwords do not match')

            # Check if username or email already exists
            if User.query.filter_by(username=username).first():
                return render_template('signup.html', error='Username already exists')
            if User.query.filter_by(email=email).first():
                return render_template('signup.html', error='Email already registered')

            # Create new user
            new_user = User(username=username, email=email)
            new_user.set_password(password)

            try:
                db.session.add(new_user)
                db.session.commit()
                return render_template('signup.html', success='Account created successfully! You can now login.')
            except Exception as e:
                db.session.rollback()
                return render_template('signup.html', error='An error occurred. Please try again.')

        return render_template('signup.html')

    @app.route('/predict', methods=["POST"])
    def predict():
        if model is None:
            return render_template(
                "index.html",
                prediction_text="Error: Model not loaded. Please contact administrator.",
                error="Model loading error"
            )

        try:
            # Get input values from form
            square_feet = float(request.form['square_feet'])
            bedrooms = int(request.form['bedrooms'])
            bathrooms = int(request.form['bathrooms'])

            # Validate inputs
            if square_feet < 0 or bedrooms < 1 or bathrooms < 1:
                raise ValueError("Invalid input values: Values must be positive")

            # Create input array for prediction
            input_data = pd.DataFrame({
                'square_feet': [square_feet],
                'bedrooms': [bedrooms],
                'bathrooms': [bathrooms]
            })
            
            # Make prediction
            prediction = model.predict(input_data)[0]

            return render_template(
                "index.html", 
                prediction_text=f"Predicted House Price: ${prediction:,.2f}",
                input_data={
                    'square_feet': square_feet,
                    'bedrooms': bedrooms,
                    'bathrooms': bathrooms
                }
            )
        except ValueError as ve:
            return render_template(
                "index.html",
                prediction_text="Invalid input. Please enter valid numbers.",
                error=str(ve)
            )
        except Exception as e:
            return render_template(
                "index.html",
                prediction_text="An error occurred during prediction.",
                error=str(e)
            )

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('500.html'), 500

    return app

app = create_app(os.getenv('FLASK_ENV', 'production')) 