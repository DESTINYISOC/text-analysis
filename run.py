"""
Development server entry point
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app
from app.config import config

# Create application instance
app = create_app(config['development'])

if __name__ == '__main__':
    app.run(
        host=os.environ.get('HOST', '0.0.0.0'),
        port=int(os.environ.get('PORT', 5000)),
        debug=True
    )