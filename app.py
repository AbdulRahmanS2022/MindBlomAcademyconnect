# app.py

import os
import json
from flask import Flask, request, jsonify
from datetime import datetime
import uuid # For generating unique IDs for database entries

# SQLAlchemy imports for database interaction
from sqlalchemy import create_engine, Column, String, Text, DateTime
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# --- Flask App Initialization ---
app = Flask(__name__)

# --- Database Configuration ---
# Render will automatically provide the DATABASE_URL environment variable
# when you link your web service to a Render PostgreSQL database.
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    # This message will appear if DATABASE_URL is not set (e.g., during local testing
    # without a .env file or proper setup).
    print("WARNING: DATABASE_URL environment variable not set. Database operations will fail.")
    # For local development, you might set a placeholder or a local SQLite URL here:
    # DATABASE_URL = "sqlite:///local_interactions.db"

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# Define the database model for your interactions
class Interaction(Base):
    """
    SQLAlchemy model for storing GPT-user interactions.
    """
    __tablename__ = 'interactions' # Name of the table in your database

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True) # Optional user identifier
    user_message = Column(Text, nullable=False) # The message from the user
    gpt_response = Column(Text, nullable=False) # The response from the GPT
    conversation_id = Column(String, nullable=True) # Optional conversation identifier
    timestamp = Column(DateTime, default=datetime.utcnow) # When the interaction occurred

    def __repr__(self):
        return f"<Interaction(id='{self.id}', user_message='{self.user_message[:30]}...')>"

# Create the table in the database if it doesn't already exist
# This will run when the app starts. In a production environment with migrations,
# you might handle this differently, but for a simple logging app, this is fine.
try:
    Base.metadata.create_all(engine)
    print("Database table 'interactions' checked/created successfully.")
except Exception as e:
    print(f"ERROR: Could not connect to database or create table: {e}")
    # You might want to exit or handle this more gracefully in a real app


# --- API Endpoint for Logging Interactions ---
@app.route('/log_interaction', methods=['POST'])
def log_interaction():
    """
    Receives user and GPT interaction data and logs it to the database.
    Requires an 'X-API-KEY' header for authentication.
    """
    # 1. Authentication Check
    expected_api_key = os.getenv('API_KEY')
    if not expected_api_key:
        print("ERROR: API_KEY environment variable not set on server.")
        return jsonify({"error": "Server configuration error: API key not set"}), 500

    incoming_api_key = request.headers.get('X-API-KEY')
    if not incoming_api_key or incoming_api_key != expected_api_key:
        print(f"Authentication failed. Incoming key: {incoming_api_key}, Expected key: {expected_api_key}")
        return jsonify({"error": "Unauthorized: Invalid API Key"}), 401

    # 2. Parse Incoming JSON Data
    data = request.get_json()
    if not data:
        print("Error: No JSON data provided in request.")
        return jsonify({"error": "No JSON data provided"}), 400

    user_message = data.get('userMessage')
    gpt_response = data.get('gptResponse')
    user_id = data.get('userId')
    conversation_id = data.get('conversationId')

    # 3. Validate Required Fields
    if not user_message or not gpt_response:
        print("Error: 'userMessage' and 'gptResponse' are required fields.")
        return jsonify({"error": "'userMessage' and 'gptResponse' are required"}), 400

    # 4. Save to Database
    session = Session()
    try:
        new_interaction = Interaction(
            user_id=user_id,
            user_message=user_message,
            gpt_response=gpt_response,
            conversation_id=conversation_id,
            timestamp=datetime.utcnow() # Ensure UTC timestamp
        )
        session.add(new_interaction)
        session.commit()
        print(f"Successfully logged interaction: User='{user_message[:50]}...', GPT='{gpt_response[:50]}...'")
        return jsonify({"status": "success", "message": "Interaction logged successfully"}), 200

    except Exception as e:
        session.rollback() # Rollback in case of error
        print(f"ERROR: Failed to log interaction to database: {e}")
        return jsonify({"error": f"Failed to log interaction: {str(e)}"}), 500
    finally:
        session.close() # Always close the session

# --- Health Check Endpoint (Optional but Recommended) ---
@app.route('/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint to confirm the API is running.
    """
    return jsonify({"status": "healthy", "message": "API is running"}), 200

# --- Local Development Server (for testing on your machine) ---
if __name__ == '__main__':
    # When running locally, you can set API_KEY in a .env file
    # and load it using `python-dotenv` (not included in requirements.txt for simplicity on Render)
    # For example: API_KEY="your_local_dev_key"
    # To run locally: python app.py
    port = int(os.getenv("PORT", 5000)) # Use Render's PORT or default to 5000
    app.run(debug=True, host='0.0.0.0', port=port)