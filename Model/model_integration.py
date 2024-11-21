import pickle
from datetime import datetime
import os

def load_model(file_path):
    with open(file_path, 'rb') as file:
        model = pickle.load(file)
    return model

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the full path to the model file
model_path = os.path.join(current_dir, 'trained_model.pkl')

# Load your model
try:
    unusual_hours_model = load_model(model_path)
    print(f"Model loaded successfully from {model_path}")
except FileNotFoundError:
    print(f"Error: Model file not found at {model_path}")
    print("Please ensure the trained model file is in the Model directory and named 'trained_model.pkl'")
    # You might want to exit the program here or handle the error in a way that makes sense for your application
    unusual_hours_model = None

def preprocess_commit_time(commit_time):
    dt = datetime.fromisoformat(commit_time.replace('Z', '+00:00'))
    hour = dt.hour
    # Adjust this based on your model's input requirements
    return [hour]

def is_unusual_commit_time(commit_time):
    if unusual_hours_model is None:
        print("Error: Model not loaded. Unable to predict unusual commit times.")
        return False
    processed_time = preprocess_commit_time(commit_time)
    prediction = unusual_hours_model.predict([processed_time])
    return prediction[0] == 1  # Returns True if unusual, False otherwise