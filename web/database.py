import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from web.extensions import db

# --- 数据模型 ---
class User(db.Model):
    __tablename__ = 'users'
    pass

class topic_info(db.Model):
    __tablename__ = 'topic_info'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cluster_id = db.Column(db.Integer, nullable=False)
    topic_name = db.Column(db.String(255), nullable=False)
    consumer_groups = db.Column(db.String(500), nullable=True)  # 存储逗号分隔的消费组列表
    partitions = db.Column(db.Integer, nullable=False)
    replication_factor = db.Column(db.Integer, nullable=False)
    disk_usage_bytes = db.Column(db.Integer, nullable=True)
    retention_ms = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.Integer, default=0)