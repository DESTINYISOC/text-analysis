"""
Routes for serving the frontend
"""
from flask import Blueprint, send_from_directory, render_template
import os

bp = Blueprint('frontend', __name__)

# Serve the frontend files
@bp.route('/')
def index():
    """Serve the main frontend page"""
    frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    return send_from_directory(frontend_path, 'index.html')

@bp.route('/<path:filename>')
def serve_frontend_file(filename):
    """Serve static files for frontend"""
    frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    return send_from_directory(frontend_path, filename)

# Also add a route at /tester for backward compatibility
@bp.route('/tester')
def tester():
    """Alternative route to the tester"""
    return index()