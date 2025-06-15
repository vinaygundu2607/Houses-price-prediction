from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import numpy as np
import joblib
import os
from config import config
import pandas as pd
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import logging
import sys
from werkzeug.exceptions import HTTPException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///users.db')
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

    # Initialize database
    try:
        with app.app_context():
            db.create_all()
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")
        # Don't raise the error, allow the app to start even if DB fails

    # Load the trained model
    try:
        model = joblib.load("model.pkl")
        logger.info("Model loaded successfully")
    except Exception as e:
        logger.error(f"Error loading model: {str(e)}")
        model = None

    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring"""
        try:
            # Check database connection
            db.session.execute('SELECT 1')
            db_status = "healthy"
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            db_status = "unhealthy"

        # Check model status
        model_status = "healthy" if model is not None else "unhealthy"

        return jsonify({
            "status": "healthy" if db_status == "healthy" and model_status == "healthy" else "degraded",
            "database": db_status,
            "model": model_status,
            "timestamp": datetime.utcnow().isoformat()
        })

    @app.route('/')
    def home():
        try:
            return render_template("index.html")
        except Exception as e:
            logger.error(f"Error rendering home page: {str(e)}")
            return render_template("500.html"), 500

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == 'POST':
            try:
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

                db.session.add(new_user)
                db.session.commit()
                return render_template('signup.html', success='Account created successfully! You can now login.')
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error during signup: {str(e)}")
                return render_template('signup.html', error='An error occurred. Please try again.')

        return render_template('signup.html')

    @app.route('/predict', methods=["POST"])
    def predict():
        if model is None:
            logger.error("Prediction attempted with no model loaded")
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
            logger.info(f"Successful prediction: {prediction}")

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
            logger.warning(f"Invalid input during prediction: {str(ve)}")
            return render_template(
                "index.html",
                prediction_text="Invalid input. Please enter valid numbers.",
                error=str(ve)
            )
        except Exception as e:
            logger.error(f"Error during prediction: {str(e)}")
            return render_template(
                "index.html",
                prediction_text="An error occurred during prediction.",
                error=str(e)
            )

    @app.errorhandler(404)
    def not_found_error(error):
        logger.warning(f"404 error: {request.url}")
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"500 error: {str(error)}")
        return render_template('500.html'), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.error(f"Unhandled exception: {str(e)}")
        if isinstance(e, HTTPException):
            return e
        return render_template('500.html'), 500

    return app

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app = create_app(os.getenv('FLASK_ENV', 'production'))
    app.run(host='0.0.0.0', port=port)
else:
    app = create_app(os.getenv('FLASK_ENV', 'production')) 