"""
Production WSGI entry point
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app import create_app
from app.config import config

app = create_app(config['production'])

if __name__ == '__main__':
    app.run()