import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

def train_and_save_model():
    print("Loading dataset...")
    # Load your dataset
    df = pd.read_csv("houses.csv")

    print("Training model...")
    # Train model
    X = df[['square_feet', 'bedrooms', 'bathrooms']]
    y = df['price']
    model = LinearRegression()
    model.fit(X, y)

    print("Saving model...")
    # Save it
    joblib.dump(model, "model.pkl")
    print("Model saved successfully!")

if __name__ == "__main__":
    train_and_save_model() 