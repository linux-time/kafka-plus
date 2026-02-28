from flask import Flask
#from flask_login import current_user
from web.extensions import  db
from web.config import config
#from web.database import User
#from flask_migrate import Migrate
#from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
#app.jinja_env.variable_start_string = '[['
#app.jinja_env.variable_end_string = ']]'
#migrate = Migrate()


#app.config['SQLALCHEMY_DATABASE_URI'] = config.db_file
app.secret_key = config.secret_key
app.config['SQLALCHEMY_DATABASE_URI'] = config.db_address
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from web.views import topic

def register_extensions(app):
    db.init_app(app)
    #migrate.init_app(app, db)

def register_blueprints(app):
#    app.register_blueprint(login.mod)
    app.register_blueprint(topic.mod)

register_extensions(app)
register_blueprints(app)