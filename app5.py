from flask import Flask, request, jsonify
from flask_cors import CORS
from commit_activity.activity import CommitsActivity
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}})  # Adjust the origin as needed

commits_activity = CommitsActivity()

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json['message']
    
    # Handle date-related queries directly
    if "date" in user_input.lower():
        current_date = datetime.now().strftime("%Y-%m-%d")
        return jsonify({'response': f"Today's date is {current_date}"})
    
    # For other queries, use the CommitsActivity
    try:
        response = commits_activity.get_answer(user_input)
        return jsonify({'response': response})
    except Exception as e:
        app.logger.error(f"Error processing request: {str(e)}")
        return jsonify({'response': "I'm sorry, I encountered an error while processing your request. Please try again."}), 500

if __name__ == '__main__':
    app.run(debug=True)