from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from commit_activity.activity import CommitsActivity
from datetime import datetime
import hmac
import hashlib
import json
import queue
import requests
import pickle
import os
import numpy as np

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})  # Adjust the origin as needed

# Hardcoded webhook secret (Note: This is not recommended for production use)
WEBHOOK_SECRET = "`123asd`123"

# GitHub API token (replace with your actual token)
GITHUB_TOKEN = "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"

# GitHub repository details
REPO_OWNER = "NIXE05"
REPO_NAME = "Test_CIS"

# Queue to store GitHub events
event_queue = queue.Queue()

commits_activity = CommitsActivity()

def load_model(file_path):
    with open(file_path, 'rb') as file:
        model = pickle.load(file)
    return model

# Get the directory of the current file
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the full path to the model file
model_path = os.path.join(current_dir, 'model', 'trained_model.pkl')

# Load your model
try:
    unusual_hours_model = load_model(model_path)
    print(f"Model loaded successfully from {model_path}")
except FileNotFoundError:
    print(f"Error: Model file not found at {model_path}")
    unusual_hours_model = None

def convert_to_serializable(obj):
    if isinstance(obj, np.generic):
        return obj.item()
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    return obj

def preprocess_commit_time(commit_time, commit_info):
    dt = datetime.fromisoformat(commit_time.replace('Z', '+00:00'))
    
    # Extract features
    access_hour = dt.hour
    hour = dt.hour
    day_of_week = dt.weekday()
    month = dt.month
    day = dt.day
    year = dt.year

    # Features that may need additional information or logic
    language = 'unknown'  # You'll need to determine how to get this information
    mode = 'unknown'  # This might require additional context about the commit
    repository = commit_info['repo']
    repository_risk = 0  # You'll need to implement logic to determine this
    unusual_hour = 0  # This should be determined by your model, not set here
    mode_category = 'unknown'  # This might require additional context

    # Convert categorical variables to numerical
    # You may need to adjust these mappings based on your model's training data
    language_map = {'unknown': 0, 'python': 1, 'javascript': 2}  # Add more as needed
    mode_map = {'unknown': 0, 'normal': 1, 'maintenance': 2}  # Add more as needed
    repository_map = {commit_info['repo']: 1}  # Add more repositories as needed
    mode_category_map = {'unknown': 0, 'development': 1, 'operations': 2}  # Add more as needed

    # Create the feature vector
    features = [
        access_hour,
        hour,
        day_of_week,
        language_map.get(language, 0),
        month,
        mode_map.get(mode, 0),
        day,
        repository_map.get(repository, 0),
        year,
        repository_risk,
        unusual_hour,
        mode_category_map.get(mode_category, 0)
    ]
    
    return np.array(features).reshape(1, -1)

def is_unusual_commit_time(commit_time, commit_info):
    if unusual_hours_model is None:
        print("Error: Model not loaded. Unable to predict unusual commit times.")
        return False
    processed_time = preprocess_commit_time(commit_time, commit_info)
    prediction = unusual_hours_model.predict(processed_time)
    return bool(prediction[0])  # Convert numpy bool to Python bool

def verify_signature(payload_body, signature):
    expected_signature = 'sha1=' + hmac.new(WEBHOOK_SECRET.encode(), payload_body, hashlib.sha1).hexdigest()
    return hmac.compare_digest(expected_signature, signature)

def get_latest_commits(count=5):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/commits"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    params = {"per_page": count}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        commits = response.json()
        return [
            {
                "type": "commit",
                "repo": REPO_NAME,
                "pusher": commit["commit"]["author"]["name"],
                "message": commit["commit"]["message"],
                "timestamp": commit["commit"]["author"]["date"]
            }
            for commit in commits
        ]
    else:
        app.logger.error(f"Failed to fetch commits: {response.status_code}")
        return []

@app.route('/webhook', methods=['POST'])
def github_webhook():
    signature = request.headers.get('X-Hub-Signature')
    if not signature or not verify_signature(request.data, signature):
        app.logger.error("Signature verification failed")
        return jsonify({"error": "Invalid signature"}), 403

    event = request.headers.get('X-GitHub-Event')
    payload = request.json

    if event == 'push':
        repo = payload['repository']['name']
        pusher = payload['pusher']['name']
        commits = payload['commits']
        
        for commit in commits:
            commit_time = commit['timestamp']
            commit_info = {
                'repo': repo,
                'pusher': pusher,
                'message': commit['message']
            }
            is_unusual = is_unusual_commit_time(commit_time, commit_info)
            commit_info.update({
                'type': 'commit',
                'timestamp': commit_time,
                'isUnusual': is_unusual
            })
            
            event_queue.put(commit_info)
            print(f"New commit added to queue: {commit_info}")
            
            if is_unusual:
                alert_info = {
                    'type': 'alert',
                    'message': f"Unusual commit detected at {commit_time} by {pusher} in {repo}"
                }
                event_queue.put(alert_info)
                print(f"Unusual commit alert added to queue: {alert_info}")
    
    return jsonify({"status": "success"}), 200

@app.route('/events', methods=['GET'])
def events():
    def generate():
        while True:
            try:
                # Get event from queue
                event = event_queue.get(timeout=30)
                serializable_event = convert_to_serializable(event)
                yield f"data: {json.dumps(serializable_event)}\n\n"
                print(f"Event sent to client: {serializable_event}")
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
                print("Keepalive sent to client")

    return Response(generate(), content_type='text/event-stream')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json['message']
    
    # Handle date-related queries directly
    if "date" in user_input.lower():
        current_date = datetime.now().strftime("%Y-%m-%d")
        return jsonify({'response': f"Today's date is {current_date}"})
    
    # Handle commit-related queries
    if "commit" in user_input.lower():
        commits = get_latest_commits()
        if commits:
            commit_messages = "\n".join([f"- {commit['message']} by {commit['pusher']} on {commit['timestamp']}" for commit in commits])
            return jsonify({'response': f"Here are the latest commits:\n{commit_messages}"})
        else:
            return jsonify({'response': "I couldn't fetch the latest commits. Please try again later."})
    
    # For other queries, use the CommitsActivity (which includes NLP functionality)
    try:
        response = commits_activity.get_answer(user_input)
        return jsonify({'response': response})
    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({'response': "I'm sorry, I encountered an error while processing your request. Please try again."}), 500

@app.route('/', methods=['GET'])
def home():
    return "GitHub Webhook and Chat Server is running!"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')