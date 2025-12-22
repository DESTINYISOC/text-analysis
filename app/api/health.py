"""
Health check endpoints
"""
from flask import Blueprint, jsonify
import psutil
import os

bp = Blueprint('health', __name__)

@bp.route('/')
def health_check():
    """Basic health check"""
    return jsonify({
        'status': 'healthy',
        'service': 'Text Augmentation API',
        'version': '1.0.0'
    })

@bp.route('/detailed')
def detailed_health():
    """Detailed health check with system info"""
    return jsonify({
        'status': 'healthy',
        'service': 'Text Augmentation API',
        'version': '1.0.0',
        'system': {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'python_version': os.sys.version
        }
    })