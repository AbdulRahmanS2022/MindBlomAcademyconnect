# netlify/functions/log_interaction_api/main.py
import os
import sys

# Add the current directory (where app.py now resides) to the Python path.
# This allows 'from app import app' to find your Flask application.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import your Flask app instance from app.py.
# Ensure your Flask app instance is named 'app' in your app.py file.
from app import app

# Import the Mangum handler, which adapts Flask (a WSGI app) to AWS Lambda events.
from mangum import Mangum

# Create the Mangum handler for your Flask app.
# This 'handler' object is what Netlify's internal Lambda environment will invoke.
handler = Mangum(app)