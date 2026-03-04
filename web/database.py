import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from web.extensions import db

# --- 数据模型 ---
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

class clusters(db.Model):
    __tablename__ = 'clusters'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cluster_name = db.Column(db.String(255))
    bootstrap_servers = db.Column(db.String(255))
    remarks = db.Column(db.String(255))

class topic_info(db.Model):
    __tablename__ = 'topic_info'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cluster_id = db.Column(db.Integer)
    topic_name = db.Column(db.String(255))
    consumer_groups = db.Column(db.String(500))  # 存储逗号分隔的消费组列表
    partitions = db.Column(db.Integer)
    replication_factor = db.Column(db.Integer)
    disk_usage_bytes = db.Column(db.Integer)
    retention_ms = db.Column(db.Integer)
    created_at = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.Integer, default=0)
    status = db.Column(db.Integer)
    remarks = db.Column(db.String(255))

class tmp_data(db.Model):
    __tablename__ = 'tmp_data'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    data_type = db.Column(db.Integer)
    data = db.Column(db.Text)
    cluster_id = db.Column(db.Integer)
    topic_id = db.Column(db.Integer)