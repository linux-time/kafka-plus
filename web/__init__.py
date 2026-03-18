import fcntl
import os
import atexit

from flask import Flask
#from flask_login import current_user
from web.extensions import  db
from web.task import scheduler
from web.config import config
#from web.database import User
from flask_migrate import Migrate
#from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
#app.jinja_env.variable_start_string = '[['
#app.jinja_env.variable_end_string = ']]'
migrate = Migrate()


app.secret_key = config.secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = config.db_address
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SCHEDULER_JOB_DEFAULTS'] = {'coalesce': True, 'max_instances': 1}
app.config['SCHEDULER_API_ENABLED'] = False

from web.views import topic
from web.views import clusters
from web.views import tasks

def register_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)

def scheduler_init(app):
    """使用文件锁确保只有一个 Gunicorn Worker 启动调度器"""
    # 在 /tmp 目录下创建一个锁文件
    lock_file = os.path.join('/tmp', f'{app.import_name}.lock')
    
    # 重点：将文件对象存为全局变量，防止被垃圾回收导致锁自动释放
    global _lock_f
    _lock_f = open(lock_file, 'wb')
    
    try:
        # 尝试获取非阻塞排他锁
        fcntl.flock(_lock_f, fcntl.LOCK_EX | fcntl.LOCK_NB)
        
        # 只有获取到锁的进程才会走到这里
        scheduler.init_app(app)
        scheduler.start()
        app.logger.info("### 定时任务已在当前进程成功启动 ###")
        
    except (BlockingIOError, IOError):
        # 锁被占用，说明已经有其他 Worker 抢到了
        _lock_f.close()
        app.logger.info("### 检测到其他进程已持有锁，当前进程跳过调度器初始化 ###")

# 注册退出清理函数
@atexit.register
def unlock_file():
    global _lock_f
    try:
        if '_lock_f' in globals() and _lock_f:
            fcntl.flock(_lock_f, fcntl.LOCK_UN)
            _lock_f.close()
    except:
        pass

def register_blueprints(app):
#    app.register_blueprint(login.mod)
    app.register_blueprint(topic.mod)
    app.register_blueprint(clusters.mod)
    app.register_blueprint(tasks.mod)

register_extensions(app)
register_blueprints(app)
scheduler_init(app)