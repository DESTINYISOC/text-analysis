"""
Standardized API response formatting
"""
from flask import jsonify
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

class APIResponse:
    """Standardized API response helper"""
    
    @staticmethod
    def success(data: Any = None, message: str = "Success", 
                status_code: int = 200, **kwargs) -> tuple:
        """
        Create a successful API response
        
        Args:
            data: Response data
            message: Success message
            status_code: HTTP status code
            **kwargs: Additional fields
            
        Returns:
            Tuple of (response_json, status_code)
        """
        response = {
            'success': True,
            'message': message,
            'data': data
        }
        response.update(kwargs)
        return jsonify(response), status_code
    
    @staticmethod
    def error(message: str, status_code: int = 400, 
              error: Optional[str] = None, errors: Optional[List] = None, 
              **kwargs) -> tuple:
        """
        Create an error API response
        
        Args:
            message: Error message
            status_code: HTTP status code
            error: Error type/description
            errors: List of validation errors
            **kwargs: Additional fields
            
        Returns:
            Tuple of (response_json, status_code)
        """
        response = {
            'success': False,
            'message': message,
            'error': error
        }
        
        if errors:
            response['errors'] = errors
        
        response.update(kwargs)
        return jsonify(response), status_code
    
    @staticmethod
    def paginated(data: List, total: int, page: int, 
                  per_page: int, **kwargs) -> tuple:
        """
        Create a paginated API response
        
        Args:
            data: List of items for current page
            total: Total number of items
            page: Current page number
            per_page: Items per page
            **kwargs: Additional fields
            
        Returns:
            Tuple of (response_json, status_code)
        """
        response = {
            'success': True,
            'data': data,
            'pagination': {
                'total': total,
                'page': page,
                'per_page': per_page,
                'pages': (total + per_page - 1) // per_page
            }
        }
        response.update(kwargs)
        return jsonify(response), 200
    
    @staticmethod
    def tier_limit_error(message: str, current_tier: str = 'free',
                        suggested_tier: str = None, upgrade_url: str = None,
                        limit_details: Dict = None, **kwargs) -> tuple:
        """
        Standard response for tier limit exceeded
        
        Args:
            message: Error message
            current_tier: User's current tier
            suggested_tier: Suggested tier to upgrade to
            upgrade_url: URL to pricing/upgrade page
            limit_details: Details about the limit that was exceeded
        """
        response = {
            'success': False,
            'message': message,
            'error': 'TierLimitExceeded',
            'current_tier': current_tier,
            'suggested_tier': suggested_tier,
            'upgrade_url': upgrade_url or '/api/v1/pricing',
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if limit_details:
            response['limit_details'] = limit_details
        
        response.update(kwargs)
        return jsonify(response), 402  # 402 Payment Required