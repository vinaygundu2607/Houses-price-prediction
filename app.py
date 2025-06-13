from flask import Flask, render_template, request
import numpy as np
import joblib
import os
from config import config

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Load the trained model
    try:
        model = joblib.load("model.pkl")
    except Exception as e:
        print(f"Error loading model: {e}")
        model = None

    @app.route('/')
    def home():
        return render_template("index.html")

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
            input_data = np.array([[square_feet, bedrooms, bathrooms]])
            
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