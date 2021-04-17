import hashlib

def convert_password(password):
    password+="qwertyyy"
    h=hashlib.sha256(password.encode("utf8")).hexdigest()
    h=hashlib.sha256(h.encode("utf8")).hexdigest()
    h=hashlib.sha256(h.encode("utf8")).hexdigest()
    return h