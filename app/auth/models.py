"""
Authentication and user management models
"""
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from dataclasses import dataclass, field
import hashlib

@dataclass
class User:
    """User model for subscription management"""
    user_id: str
    email: str
    tier: str = 'free'  # free, basic, pro, enterprise
    created_at: datetime = field(default_factory=datetime.utcnow)
    subscription_id: Optional[str] = None
    subscription_start: Optional[datetime] = None
    subscription_end: Optional[datetime] = None
    monthly_requests: int = 0
    daily_requests: Dict[str, int] = field(default_factory=dict)  # date -> count
    total_requests: int = 0
    
    def __post_init__(self):
        if not self.user_id:
            self.user_id = f"user_{secrets.token_hex(8)}"
    
    def generate_api_key(self, name: str = 'default') -> str:
        """Generate a new API key for this user"""
        api_key = f"ta_{secrets.token_hex(24)}"
        return api_key
    
    def can_make_request(self, feature: str = None, **kwargs) -> Dict[str, any]:
        """
        Check if user can make a request based on their tier
        
        Returns:
            Dict with 'allowed' boolean and 'message' if not allowed
        """
        today = datetime.utcnow().date().isoformat()
        
        # Initialize daily counter if not exists
        if today not in self.daily_requests:
            self.daily_requests[today] = 0
        
        # Get tier limits
        limits = self.get_tier_limits()
        
        # Check daily request limit
        if self.daily_requests[today] >= limits['daily_requests']:
            return {
                'allowed': False,
                'message': f'Daily request limit exceeded ({limits["daily_requests"]}). Please upgrade or try again tomorrow.',
                'upgrade_url': '/api/v1/pricing'
            }
        
        # Check specific feature limits
        if feature == 'augmentation':
            augmentation_count = kwargs.get('augmentation_count', 1)
            if augmentation_count > limits['max_augmentations']:
                return {
                    'allowed': False,
                    'message': f'Free tier allows maximum {limits["max_augmentations"]} augmentations. You requested {augmentation_count}.',
                    'suggested_tier': 'basic' if augmentation_count <= 10 else 'pro',
                    'upgrade_url': '/api/v1/pricing'
                }
        
        elif feature == 'batch':
            batch_size = kwargs.get('batch_size', 1)
            if batch_size > limits['batch_limit']:
                return {
                    'allowed': False,
                    'message': f'Free tier allows maximum {limits["batch_limit"]} texts per batch. You requested {batch_size}.',
                    'suggested_tier': 'basic' if batch_size <= 10 else 'pro',
                    'upgrade_url': '/api/v1/pricing'
                }
        
        elif feature == 'text_length':
            text_length = kwargs.get('text_length', 0)
            if text_length > limits['max_text_length']:
                return {
                    'allowed': False,
                    'message': f'Free tier allows maximum {limits["max_text_length"]} characters. Your text has {text_length}.',
                    'suggested_tier': 'basic' if text_length <= 2000 else 'pro',
                    'upgrade_url': '/api/v1/pricing'
                }
        
        elif feature == 'premium_feature':
            return {
                'allowed': False,
                'message': 'This is a premium feature. Upgrade to Basic tier or higher.',
                'required_tier': 'basic',
                'upgrade_url': '/api/v1/pricing'
            }
        
        return {'allowed': True, 'message': 'Request allowed'}
    
    def get_tier_limits(self) -> Dict[str, any]:
        """Get limits for user's current tier"""
        tier_configs = {
            'free': {
                'daily_requests': 100,
                'max_augmentations': 3,
                'batch_limit': 1,
                'max_text_length': 500,
                'features': ['enrich_text', 'sentiment_analysis'],
                'monthly_price': 0,
                'yearly_price': 0
            },
            'basic': {
                'daily_requests': 1000,
                'max_augmentations': 10,
                'batch_limit': 10,
                'max_text_length': 2000,
                'features': ['enrich_text', 'sentiment_analysis', 'batch_processing', 'tone_analysis'],
                'monthly_price': 9.99,
                'yearly_price': 99.99
            },
            'pro': {
                'daily_requests': 10000,
                'max_augmentations': 50,
                'batch_limit': 100,
                'max_text_length': 10000,
                'features': ['enrich_text', 'sentiment_analysis', 'batch_processing', 
                            'summarization', 'keyword_extraction', 'priority_support'],
                'monthly_price': 29.99,
                'yearly_price': 299.99
            },
            'enterprise': {
                'daily_requests': 100000,
                'max_augmentations': 200,
                'batch_limit': 1000,
                'max_text_length': 50000,
                'features': 'all',
                'monthly_price': 99.99,
                'yearly_price': 999.99
            }
        }
        
        return tier_configs.get(self.tier, tier_configs['free'])
    
    def increment_request_count(self):
        """Increment request counters"""
        today = datetime.utcnow().date().isoformat()
        self.daily_requests[today] = self.daily_requests.get(today, 0) + 1
        self.total_requests += 1
    
    def upgrade_tier(self, new_tier: str, subscription_id: str = None):
        """Upgrade user to a new tier"""
        allowed_tiers = ['free', 'basic', 'pro', 'enterprise']
        if new_tier in allowed_tiers:
            old_tier = self.tier
            self.tier = new_tier
            self.subscription_id = subscription_id
            self.subscription_start = datetime.utcnow()
            
            # Set subscription end (30 days from now for monthly)
            self.subscription_end = datetime.utcnow() + timedelta(days=30)
            
            return True
        return False

@dataclass
class APIKey:
    """API Key model"""
    key: str
    user_id: str
    name: str = 'default'
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    is_active: bool = True
    request_count: int = 0
    
    def is_valid(self) -> bool:
        """Check if API key is valid"""
        return self.is_active
    
    def record_usage(self):
        """Record that this key was used"""
        self.last_used = datetime.utcnow()
        self.request_count += 1

class UserManager:
    """Manages users and API keys"""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self.api_keys: Dict[str, APIKey] = {}
        self.email_to_user: Dict[str, str] = {}
    
    def create_user(self, email: str, tier: str = 'free') -> User:
        """Create a new user"""
        if email in self.email_to_user:
            return self.users[self.email_to_user[email]]
        
        user = User(user_id=f"user_{secrets.token_hex(8)}", email=email, tier=tier)
        self.users[user.user_id] = user
        self.email_to_user[email] = user.user_id
        
        # Generate default API key
        api_key = user.generate_api_key()
        self.api_keys[api_key] = APIKey(key=api_key, user_id=user.user_id)
        
        return user
    
    def get_user_by_api_key(self, api_key: str) -> Optional[User]:
        """Get user by API key"""
        if api_key in self.api_keys:
            api_key_obj = self.api_keys[api_key]
            if api_key_obj.is_valid():
                api_key_obj.record_usage()
                return self.users.get(api_key_obj.user_id)
        return None
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        user_id = self.email_to_user.get(email)
        return self.users.get(user_id) if user_id else None
    
    def generate_api_key_for_user(self, user_id: str, name: str = 'default') -> str:
        """Generate a new API key for a user"""
        if user_id not in self.users:
            return None
        
        api_key = f"ta_{secrets.token_hex(24)}"
        self.api_keys[api_key] = APIKey(key=api_key, user_id=user_id, name=name)
        return api_key
    
    def validate_request(self, api_key: str, feature: str = None, **kwargs) -> Dict[str, any]:
        """
        Validate if a request is allowed
        
        Returns:
            Dict with validation result
        """
        user = self.get_user_by_api_key(api_key)
        
        if not user:
            # Anonymous user (free tier without API key)
            user = User(user_id='anonymous', email='anonymous@example.com', tier='free')
        
        # Check if request is allowed
        validation = user.can_make_request(feature, **kwargs)
        
        if validation['allowed']:
            user.increment_request_count()
        
        validation['user'] = user
        validation['tier'] = user.tier
        validation['daily_requests_used'] = user.daily_requests.get(
            datetime.utcnow().date().isoformat(), 0
        )
        validation['daily_requests_limit'] = user.get_tier_limits()['daily_requests']
        
        return validation

# Global user manager instance
user_manager = UserManager()

# Create some test users
def create_test_users():
    """Create test users for development"""
    test_users = [
        ('free_user@example.com', 'free'),
        ('basic_user@example.com', 'basic'),
        ('pro_user@example.com', 'pro'),
        ('enterprise_user@example.com', 'enterprise')
    ]
    
    for email, tier in test_users:
        user_manager.create_user(email, tier)
    
    # Also create anonymous user for testing without API key
    user_manager.users['anonymous'] = User(
        user_id='anonymous', 
        email='anonymous@example.com', 
        tier='free'
    )

# Initialize test users
create_test_users()