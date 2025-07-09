"""
Authentication Middleware for AI Buddy Backend

This middleware protects routes with Clerk authentication.
Provides decorators for requiring authentication and extracting user info.
"""

import logging
from functools import wraps
from typing import Optional, Dict, Any

from flask import request, jsonify, g
from services.clerk_auth_service import clerk_auth_service

logger = logging.getLogger(__name__)

def require_auth(f):
    """
    Decorator that requires Clerk authentication for endpoint access
    
    Usage:
        @app.route('/protected-endpoint')
        @require_auth
        def protected_endpoint():
            # Access user info via g.user
            user_id = g.user['user_id']
            return jsonify({'message': 'Hello authenticated user!'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'success': False,
                'error': 'missing_authorization',
                'message': 'Authorization header is required'
            }), 401
        
        # Check if it's a Bearer token
        if not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': 'invalid_token_format',
                'message': 'Authorization header must start with "Bearer "'
            }), 401
        
        # Extract token
        token = auth_header.split(' ')[1]
        
        # Verify token with Clerk
        user_info = clerk_auth_service.verify_token(token)
        
        if not user_info:
            return jsonify({
                'success': False,
                'error': 'invalid_token',
                'message': 'Invalid or expired token'
            }), 401
        
        # Store user info in Flask's g object for use in endpoint
        g.user = user_info
        
        return f(*args, **kwargs)
    
    return decorated_function

def optional_auth(f):
    """
    Decorator that optionally includes user info if authenticated
    
    Usage:
        @app.route('/public-endpoint')
        @optional_auth
        def public_endpoint():
            # Check if user is authenticated
            if hasattr(g, 'user') and g.user:
                return jsonify({'message': f'Hello {g.user["first_name"]}!'})
            else:
                return jsonify({'message': 'Hello anonymous user!'})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Extract token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            user_info = clerk_auth_service.verify_token(token)
            
            if user_info:
                g.user = user_info
        
        return f(*args, **kwargs)
    
    return decorated_function

def get_current_user() -> Optional[Dict[str, Any]]:
    """
    Helper function to get current user from Flask's g object
    
    Returns:
        Dict with user info or None if not authenticated
    """
    return getattr(g, 'user', None)

def extract_user_id() -> Optional[str]:
    """
    Helper function to extract user ID from current user
    
    Returns:
        User ID string or None if not authenticated
    """
    user = get_current_user()
    return user.get('user_id') if user else None 