"""
Authentication APIs and middleware
"""

from functools import wraps
from flask import request, jsonify
from database import db
import logging

logger = logging.getLogger(__name__)


def get_token_from_request():
    """Extract token from request header"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    # Format: "Bearer <token>"
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    return parts[1]


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'Missing authentication token'
            }), 401
        
        session = db.verify_token(token)
        
        if not session:
            return jsonify({
                'success': False,
                'error': 'Invalid or expired token'
            }), 401
        
        # Add user info to request context
        request.user_id = session['user_id']
        request.user_email = session['email']
        request.user_role = session['role']
        
        return f(*args, **kwargs)
    
    return decorated_function


def require_admin(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'Missing authentication token'
            }), 401
        
        session = db.verify_token(token)
        
        if not session:
            return jsonify({
                'success': False,
                'error': 'Invalid or expired token'
            }), 401
        
        if session['role'] != 'admin':
            return jsonify({
                'success': False,
                'error': 'Admin access required'
            }), 403
        
        # Add user info to request context
        request.user_id = session['user_id']
        request.user_email = session['email']
        request.user_role = session['role']
        
        return f(*args, **kwargs)
    
    return decorated_function


def get_client_ip():
    """Get client IP address"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0]
    return request.remote_addr


def get_device_info():
    """Get device information from headers"""
    return {
        'user_agent': request.headers.get('User-Agent'),
        'platform': request.headers.get('X-Platform'),  # Custom header from app
        'app_version': request.headers.get('X-App-Version')  # Custom header from app
    }
