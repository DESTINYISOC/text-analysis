"""
Flask extensions initialization
"""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flasgger import Swagger

# Rate limiter
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per hour"],
    storage_uri="memory://",
    strategy="fixed-window",  # or "moving-window"
    enabled=True
)

# Swagger
swagger = Swagger()