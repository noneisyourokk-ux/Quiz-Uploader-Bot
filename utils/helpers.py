import config

def is_admin(user_id: int) -> bool:
    """Checks if a user is in the configured ADMIN_IDS list."""
    if not config.ADMIN_IDS:
        return True  # If no admin ID is set, allow all (or set to False for strict security)
    return user_id in config.ADMIN_IDS
