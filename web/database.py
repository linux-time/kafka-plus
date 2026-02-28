import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from web.extensions import db

# --- 数据模型 ---
class User(db.Model):
    __tablename__ = 'users'
    pass

class Paste(db.Model):
    __tablename__ = 'pastes'
    pass