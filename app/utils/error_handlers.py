"""
Custom error handlers for the Flask application
"""
from flask import jsonify
from app.utils.response import APIResponse

def register_error_handlers(app):
    """
    Register custom error handlers for the Flask application
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors"""
        return APIResponse.error(
            message="Bad Request",
            error="The server could not understand the request due to invalid syntax.",
            status_code=400
        )
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors"""
        return APIResponse.error(
            message="Not Found",
            error="The requested resource was not found on this server.",
            status_code=404
        )
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed errors"""
        return APIResponse.error(
            message="Method Not Allowed",
            error="The method is not allowed for the requested URL.",
            status_code=405
        )
    
    @app.errorhandler(429)
    def too_many_requests(error):
        """Handle 429 Too Many Requests errors"""
        return APIResponse.error(
            message="Too Many Requests",
            error="Rate limit exceeded. Please try again later.",
            status_code=429
        )
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server Error"""
        # Log the error here if needed
        app.logger.error(f"Internal Server Error: {error}")
        
        return APIResponse.error(
            message="Internal Server Error",
            error="An unexpected error occurred on the server.",
            status_code=500
        )
    
    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Catch-all handler for unexpected exceptions"""
        app.logger.error(f"Unexpected error: {error}")
        
        return APIResponse.error(
            message="Unexpected Error",
            error="An unexpected error occurred.",
            status_code=500
        )