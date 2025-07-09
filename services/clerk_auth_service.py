"""
Clerk Authentication Service for AI Buddy Backend

This service handles user authentication using Clerk's SMS/Phone authentication.
Provides endpoints for phone number verification and user management.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from clerk_backend_sdk import Clerk
from clerk_backend_sdk.exceptions import ClerkException
from flask import request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ClerkAuthService:
    """Service for handling Clerk authentication operations"""
    
    def __init__(self):
        """Initialize Clerk client with API credentials"""
        self.clerk_secret_key = os.getenv('CLERK_SECRET_KEY')
        self.clerk_publishable_key = os.getenv('CLERK_PUBLISHABLE_KEY')
        
        if not self.clerk_secret_key:
            raise ValueError("CLERK_SECRET_KEY environment variable is required")
        
        # Initialize Clerk client
        self.clerk = Clerk(bearer_auth=self.clerk_secret_key)
        
        logger.info("✅ Clerk Authentication Service initialized")
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify a Clerk session token and return user information
        
        Args:
            token: Clerk session token from client
            
        Returns:
            Dict containing user information or None if invalid
        """
        try:
            # Verify the token using Clerk's verify_token method
            verification = self.clerk.verify_token(token)
            
            if verification and verification.get('sub'):
                # Get user details from Clerk
                user_id = verification['sub']
                user = self.clerk.users.get(user_id)
                
                return {
                    'user_id': user_id,
                    'phone_number': user.phone_numbers[0].phone_number if user.phone_numbers else None,
                    'email': user.email_addresses[0].email_address if user.email_addresses else None,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'created_at': user.created_at,
                    'updated_at': user.updated_at,
                    'verified': any(phone.verification.status == 'verified' for phone in user.phone_numbers)
                }
            
            return None
            
        except ClerkException as e:
            logger.warning(f"Token verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {e}")
            return None
    
    def create_phone_number_verification(self, phone_number: str) -> Dict[str, Any]:
        """
        Create a phone number verification (send SMS code)
        
        Args:
            phone_number: Phone number to verify (E.164 format)
            
        Returns:
            Dict with verification details
        """
        try:
            # Create phone number verification
            verification = self.clerk.phone_numbers.create(
                phone_number=phone_number
            )
            
            # Prepare verification for SMS
            verification_attempt = self.clerk.phone_numbers.create_verification(
                phone_number_id=verification.id,
                strategy="sms_code"
            )
            
            logger.info(f"SMS verification code sent to {phone_number}")
            
            return {
                'success': True,
                'verification_id': verification.id,
                'phone_number': phone_number,
                'status': verification_attempt.status,
                'message': 'Verification code sent via SMS'
            }
            
        except ClerkException as e:
            logger.error(f"Failed to create phone verification: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to send verification code'
            }
        except Exception as e:
            logger.error(f"Unexpected error creating phone verification: {e}")
            return {
                'success': False,
                'error': 'Internal server error',
                'message': 'Failed to send verification code'
            }
    
    def verify_phone_number(self, phone_number_id: str, code: str) -> Dict[str, Any]:
        """
        Verify phone number with SMS code
        
        Args:
            phone_number_id: ID from phone number creation
            code: SMS verification code
            
        Returns:
            Dict with verification result
        """
        try:
            # Attempt to verify the phone number
            verification = self.clerk.phone_numbers.attempt_verification(
                phone_number_id=phone_number_id,
                code=code
            )
            
            if verification.status == 'verified':
                logger.info(f"Phone number {phone_number_id} successfully verified")
                return {
                    'success': True,
                    'verified': True,
                    'phone_number': verification.phone_number,
                    'message': 'Phone number verified successfully'
                }
            else:
                return {
                    'success': False,
                    'verified': False,
                    'message': 'Invalid verification code'
                }
                
        except ClerkException as e:
            logger.error(f"Phone verification failed: {e}")
            return {
                'success': False,
                'verified': False,
                'error': str(e),
                'message': 'Verification failed'
            }
        except Exception as e:
            logger.error(f"Unexpected error during phone verification: {e}")
            return {
                'success': False,
                'verified': False,
                'error': 'Internal server error',
                'message': 'Verification failed'
            }
    
    def create_user_session(self, phone_number: str) -> Dict[str, Any]:
        """
        Create a user session after successful phone verification
        
        Args:
            phone_number: Verified phone number
            
        Returns:
            Dict with session token and user info
        """
        try:
            # Find user by phone number
            users = self.clerk.users.list(phone_number=[phone_number])
            
            if users.data:
                user = users.data[0]
                
                # Create session for existing user
                session = self.clerk.sessions.create(
                    user_id=user.id
                )
                
                return {
                    'success': True,
                    'session_token': session.id,
                    'user': {
                        'id': user.id,
                        'phone_number': phone_number,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'created_at': user.created_at
                    },
                    'message': 'Session created successfully'
                }
            else:
                # Create new user
                user = self.clerk.users.create(
                    phone_number=[phone_number]
                )
                
                # Create session for new user
                session = self.clerk.sessions.create(
                    user_id=user.id
                )
                
                return {
                    'success': True,
                    'session_token': session.id,
                    'user': {
                        'id': user.id,
                        'phone_number': phone_number,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'created_at': user.created_at
                    },
                    'message': 'User created and session established'
                }
                
        except ClerkException as e:
            logger.error(f"Failed to create user session: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to create session'
            }
        except Exception as e:
            logger.error(f"Unexpected error creating user session: {e}")
            return {
                'success': False,
                'error': 'Internal server error',
                'message': 'Failed to create session'
            }
    
    def get_user_info(self, user_id: str) -> Dict[str, Any]:
        """
        Get user information from Clerk
        
        Args:
            user_id: Clerk user ID
            
        Returns:
            Dict with user information
        """
        try:
            user = self.clerk.users.get(user_id)
            
            return {
                'success': True,
                'user': {
                    'id': user.id,
                    'phone_number': user.phone_numbers[0].phone_number if user.phone_numbers else None,
                    'email': user.email_addresses[0].email_address if user.email_addresses else None,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'created_at': user.created_at,
                    'updated_at': user.updated_at,
                    'verified': any(phone.verification.status == 'verified' for phone in user.phone_numbers)
                }
            }
            
        except ClerkException as e:
            logger.error(f"Failed to get user info: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to retrieve user information'
            }
        except Exception as e:
            logger.error(f"Unexpected error getting user info: {e}")
            return {
                'success': False,
                'error': 'Internal server error',
                'message': 'Failed to retrieve user information'
            }
    
    def revoke_session(self, session_id: str) -> Dict[str, Any]:
        """
        Revoke a user session (logout)
        
        Args:
            session_id: Session ID to revoke
            
        Returns:
            Dict with result
        """
        try:
            self.clerk.sessions.revoke(session_id)
            
            return {
                'success': True,
                'message': 'Session revoked successfully'
            }
            
        except ClerkException as e:
            logger.error(f"Failed to revoke session: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Failed to revoke session'
            }
        except Exception as e:
            logger.error(f"Unexpected error revoking session: {e}")
            return {
                'success': False,
                'error': 'Internal server error',
                'message': 'Failed to revoke session'
            }

# Global instance
clerk_auth_service = ClerkAuthService() 