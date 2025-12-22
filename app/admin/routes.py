from flask import Blueprint, render_template, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import secrets

from app.auth.models import APIKeyManager
from app.analytics.tracker import AnalyticsTracker

bp = Blueprint('admin', __name__)
limiter = Limiter(key_func=get_remote_address)

# Simple admin authentication (use proper auth in production)
ADMIN_TOKEN = "admin_" + secrets.token_hex(16)

@bp.route('/dashboard', methods=['GET'])
def admin_dashboard():
    """Admin dashboard (protected)"""
    token = request.args.get('token')
    
    if token != ADMIN_TOKEN:
        return jsonify({'error': 'Unauthorized'}), 401
    
    # Get system stats
    tracker = AnalyticsTracker()
    system_stats = tracker.get_system_stats()
    
    # Get user stats
    api_manager = APIKeyManager()
    user_stats = []
    for user_id, user in api_manager.users.items():
        user_stats.append({
            'user_id': user_id,
            'email': user.email,
            'tier': user.tier,
            'requests_today': user.usage_stats['requests_today'],
            'total_requests': user.usage_stats['requests_month']
        })
    
    return jsonify({
        'system_stats': system_stats,
        'user_stats': user_stats,
        'total_users': len(api_manager.users),
        # 'revenue_estimate': self._calculate_revenue_estimate(api_manager.users)
        'revenue_estimate': _calculate_revenue_estimate(api_manager.users)
    })

def _calculate_revenue_estimate(users):
    """Calculate estimated monthly revenue"""
    tier_prices = {
        'free': 0,
        'basic': 9.99,
        'pro': 29.99,
        'enterprise': 99.99
    }
    
    revenue = 0
    for user in users.values():
        revenue += tier_prices.get(user.tier, 0)
    
    return round(revenue, 2)