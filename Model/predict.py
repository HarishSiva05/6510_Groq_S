import sys
import json
import joblib
import numpy as np
import os
import pandas as pd
import pickle

# Define the exact feature order used during training
feature_names = [
    'access_hour', 'hour', 'day_of_week', 'language', 'month',
    'mode', 'day', 'repository', 'year', 'repository_risk',
    'unusual_hour', 'mode_category'
]

# Load the model
model_path = r"C:\Courses\Chatbot_Project\Python\trained_model.pkl"
model = joblib.load(model_path)

# Load the target encoder
encoder_path = r"C:\Courses\Chatbot_Project\Python\target_encoder.pkl"
with open(encoder_path, "rb") as f:
    target_encoder = pickle.load(f)

# Preprocess input
def preprocess_input(input_data):
    # Fill missing values
    input_data["language"] = input_data.get("language", "Unknown")
    input_data["repository"] = input_data.get("repository", "Unknown")

    # Target encode 'language' and 'repository'
    try:
        encoding_input = pd.DataFrame([{
            "language": input_data["language"],
            "repository": input_data["repository"]
        }])
        encoded_values = target_encoder.transform(encoding_input)
        input_data["language"] = encoded_values["language"].iloc[0]
        input_data["repository"] = encoded_values["repository"].iloc[0]
    except Exception as e:
        print(json.dumps({"error": f"Target encoding failed: {e}"}))
        sys.exit(1)

    # Reorder features to match training order
    features = {name: input_data.get(name, 0) for name in feature_names}
    return pd.DataFrame([features])

# Read input from stdin
try:
    input_data = sys.stdin.read()
    parsed_data = json.loads(input_data)
except Exception as e:
    print(json.dumps({"error": f"Invalid input: {e}"}))
    sys.exit(1)

# Preprocess input data
try:
    features_df = preprocess_input(parsed_data)
except Exception as e:
    print(json.dumps({"error": f"Preprocessing failed: {e}"}))
    sys.exit(1)

# Make predictions
try:
    prediction = model.predict(features_df)
    print(json.dumps({"prediction": prediction.tolist()}))
except Exception as e:
    print(json.dumps({"error": f"Prediction failed: {e}"}))
    sys.exit(1)
