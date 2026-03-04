import fcntl

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


#app.config['SQLALCHEMY_DATABASE_URI'] = config.db_file
app.secret_key = config.secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = config.db_address
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SCHEDULER_JOB_DEFAULTS'] = {'coalesce': True, 'max_instances': 1}
app.config['SCHEDULER_API_ENABLED'] = False

from web.views import topic
from web.views import clusters

def register_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)

def scheduler_init(app):
    lock_file = '/tmp/scheduler.lock'  # 锁文件路径
    try:
        with open(lock_file, 'wb') as f:
            fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)  # 尝试获取文件锁
            scheduler.init_app(app)
            scheduler.start()
    except BlockingIOError:
        # 如果无法获取锁，说明其他进程正在运行任务
        print("任务已在其他进程中运行，跳过本次执行")

def register_blueprints(app):
#    app.register_blueprint(login.mod)
    app.register_blueprint(topic.mod)
    app.register_blueprint(clusters.mod)

register_extensions(app)
register_blueprints(app)
scheduler_init(app)