import os
import sqlite3
from flask import Flask, request, jsonify, render_template, session
from memory import create_runner

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super-secret-key")

# Initialize ADK Runner
runner = create_runner()

def init_db():
    conn = sqlite3.connect('sessions.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS sessions
                 (session_id TEXT PRIMARY KEY, user_data TEXT)''')
    conn.commit()
    conn.close()

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message')
    session_id = session.get('session_id', 'default_session')
    
    # Check for identity verification flow (placeholder logic)
    if "verify" in user_input.lower():
        return jsonify({"response": "Guest verification started. Please provide your ID."})
        
    try:
        # Pass the input to the ADK Runner
        # The runner handles orchestration among specialized agents
        # ADK 2.1.0 Runner.run expects new_message as Content
        from google.genai._transformers import t_content
        
        events = runner.run(
            user_id="default_user",
            session_id=session_id,
            new_message=t_content(user_input)
        )
        
        # Consume the generator to get the final response
        final_response = ""
        for event in events:
            if event.message and event.message.parts:
                for part in event.message.parts:
                    if part.text:
                        final_response += part.text
                        
        if not final_response:
            final_response = "Agents are working on your request..."
                
        return jsonify({"response": str(final_response)})
    except Exception as e:
        return jsonify({"response": f"Error: {str(e)}"}), 500

@app.route('/assets', methods=['GET'])
def get_assets():
    # Placeholder for asset library retrieval
    return jsonify({"assets": [
        {"id": 1, "name": "Minimalist Pastel Ad", "url": "/static/ad1.jpg"},
        {"id": 2, "name": "Cyberpunk Neon Variant", "url": "/static/ad2.jpg"}
    ]})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
