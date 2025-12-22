import stripe
from datetime import datetime

class StripePaymentManager:
    """Stripe payment integration"""
    
    def __init__(self, api_key: str):
        stripe.api_key = api_key
        self.plans = {
            'basic': 'price_basic_monthly',
            'pro': 'price_pro_monthly',
            'enterprise': 'price_enterprise_monthly'
        }
    
    def create_checkout_session(self, user_id: str, tier: str, success_url: str, 
                               cancel_url: str) -> dict:
        """Create a Stripe checkout session"""
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': self.plans[tier],
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    'user_id': user_id,
                    'tier': tier
                }
            )
            return {'success': True, 'session_id': session.id, 'url': session.url}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def handle_webhook(self, payload: str, sig_header: str, webhook_secret: str) -> dict:
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
            
            if event['type'] == 'checkout.session.completed':
                session = event['data']['object']
                user_id = session['metadata']['user_id']
                tier = session['metadata']['tier']
                
                # Update user tier in database
                return {
                    'success': True,
                    'user_id': user_id,
                    'tier': tier,
                    'action': 'upgrade_user'
                }
            
            return {'success': True, 'event': event['type']}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}