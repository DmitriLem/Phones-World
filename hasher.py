import hashlib

def hash_password(password):
    password_bytes = password.encode('utf-8')
    hasher = hashlib.sha256()
    hasher.update(password_bytes)
    hashed_password = hasher.hexdigest()
    return hashed_password