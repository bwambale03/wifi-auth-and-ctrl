import random
import string

def generate_random_code(length=12):
    """Generate a random alphanumeric code of specified length."""
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))
