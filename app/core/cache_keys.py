"""Cache key generation utilities."""

def get_user_cache_key(user_id: int) -> str:
    """Generate cache key for a specific user."""
    return f"user:{user_id}"

def get_users_list_cache_key(skip: int = 0, limit: int = 100) -> str:
    """Generate cache key for users list."""
    return f"users:list:skip={skip}:limit={limit}"

def get_user_by_username_cache_key(username: str) -> str:
    """Generate cache key for user by username."""
    return f"user:username:{username}"

def get_user_by_email_cache_key(email: str) -> str:
    """Generate cache key for user by email."""
    return f"user:email:{email}"