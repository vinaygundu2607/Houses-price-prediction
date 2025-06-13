import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

def load_and_prepare_data():
    # Load the dataset
    df = pd.read_csv('houses.csv')
    
    # Check for missing values
    print("\nMissing values in the dataset:")
    print(df.isnull().sum())
    
    # Drop rows with missing values if any
    df.dropna(inplace=True)
    
    # Define features and target
    X = df[['square_feet', 'bedrooms', 'bathrooms']]
    y = df['price']
    
    return X, y

def train_model(X, y):
    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Create and train the model
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Make predictions on test set
    y_pred = model.predict(X_test)
    
    # Calculate metrics
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    
    print("\nModel Performance:")
    print(f"Mean Squared Error: {mse:.2f}")
    print(f"R² Score: {r2:.2f}")
    
    return model, X_test, y_test

def predict_price(model, square_feet, bedrooms, bathrooms):
    # Make prediction for a new house
    new_house = [[square_feet, bedrooms, bathrooms]]
    predicted_price = model.predict(new_house)
    return predicted_price[0]

def main():
    print("House Price Prediction Model")
    print("===========================")
    
    # Load and prepare data
    X, y = load_and_prepare_data()
    
    # Train model and get performance metrics
    model, X_test, y_test = train_model(X, y)
    
    # Example prediction
    example_house = {
        'square_feet': 2000,
        'bedrooms': 3,
        'bathrooms': 2
    }
    
    predicted_price = predict_price(
        model,
        example_house['square_feet'],
        example_house['bedrooms'],
        example_house['bathrooms']
    )
    
    print("\nExample Prediction:")
    print(f"House details: {example_house}")
    print(f"Predicted price: ${predicted_price:,.2f}")
    
    # Print model coefficients
    print("\nModel Coefficients:")
    feature_names = ['square_feet', 'bedrooms', 'bathrooms']
    for name, coef in zip(feature_names, model.coef_):
        print(f"{name}: ${coef:,.2f}")
    print(f"Intercept: ${model.intercept_:,.2f}")

if __name__ == "__main__":
    main() 