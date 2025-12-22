"""
Input validation for API requests
"""
import re
from typing import Dict, Any

class Validator:
    """Input validation utilities"""
    
    @staticmethod
    def validate_enrich_request(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate the enrich text request
        
        Args:
            data: Request JSON data
            
        Returns:
            Dictionary with validation results
        """
        errors = []
        
        # Check if text field exists
        if 'text' not in data:
            errors.append("Missing required field: 'text'")
            return {
                'valid': False,
                'errors': errors,
                'message': 'Validation failed'
            }
        
        text = data.get('text', '')
        
        # Validate text type and length
        if not isinstance(text, str):
            errors.append("'text' must be a string")
        elif not text.strip():
            errors.append("'text' cannot be empty or whitespace only")
        elif len(text.strip()) < 2:
            errors.append("'text' must be at least 2 characters long")
        elif len(text.strip()) > 1000:  # From config
            errors.append("'text' exceeds maximum length of 1000 characters")
        
        # Validate augmentation_count if provided
        augmentation_count = data.get('augmentation_count', 3)
        if not isinstance(augmentation_count, int):
            errors.append("'augmentation_count' must be an integer")
        elif augmentation_count < 1:
            errors.append("'augmentation_count' must be at least 1")
        elif augmentation_count > 10:  # From config
            errors.append("'augmentation_count' cannot exceed 10")
        
        # Check for potentially malicious content (basic check)
        if text and Validator._contains_malicious_content(text):
            errors.append("Text contains potentially harmful content")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors if errors else None,
            'message': 'Validation successful' if not errors else 'Validation failed'
        }
    
    @staticmethod
    def _contains_malicious_content(text: str) -> bool:
        """
        Basic check for potentially malicious content
        
        Args:
            text: Text to check
            
        Returns:
            True if potentially malicious content is found
        """
        # Simple patterns to detect potential injection attempts
        malicious_patterns = [
            r'<script.*?>.*?</script>',  # Script tags
            r'on\w+\s*=',                # Event handlers
            r'javascript:',               # JavaScript protocol
            r'data:',                     # Data protocol
            r'vbscript:',                 # VBScript protocol
        ]
        
        for pattern in malicious_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        return False

# Convenience function
def validate_enrich_request(data):
    """Wrapper function for the Validator class"""
    return Validator.validate_enrich_request(data)