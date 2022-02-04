from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_login import LoginManager
from flask_moment import Moment
from flask_pagedown import PageDown
from config import config
from flask_caching import Cache
from flask_cors import CORS
from flask_mongoengine import MongoEngine
from flask_admin import Admin
from celery import Celery
import logging

logger = logging.getLogger(__name__)

db = MongoEngine()
app_admin = Admin(name='MolSSI COVID APIs Admin', template_mode='bootstrap3',
                  base_template='admin/custom_base.html')


bootstrap = Bootstrap()
mail = Mail()
pagedown = PageDown()
moment = Moment()  # formatting dates and time
cache = Cache()
cors = CORS()

login_manager = LoginManager()
login_manager.login_view = 'auth.login'


def create_app(config_name):
    logger.info(f"logger: Creating flask app with config {config_name}")

    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    logger.info(f'Using Cache Type: {app.config["CACHE_TYPE"]}')

    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)
    cache.init_app(app)
    cors.init_app(app)


    if app.config['SSL_REDIRECT']:
        from flask_sslify import SSLify
        sslify = SSLify(app)

    with app.app_context():

        logger.debug("Adding blueprints..")
        # The main application entry
        from .main import main as main_blueprint
        app.register_blueprint(main_blueprint)

        # For authentication
        from .auth import auth as auth_blueprint
        app.register_blueprint(auth_blueprint, url_prefix='/auth')

        # # API if needed
        # from .api import api as api_blueprint
        # app.register_blueprint(api_blueprint, url_prefix='/api/v1')

        # create user roles
        from .models.users import update_roles
        update_roles()

        # To avoid circular import
        from app.admin import add_admin_views
        add_admin_views()

        # Then init the app
        app_admin.init_app(app)


        # Compile assets (JS, SCSS, less)
        logger.debug('Creating assets..')
        from .assets import compile_assets
        compile_assets(app)
        logger.debug('App Ready..')

        return app

    return app


# URL here is the name of the docker-compose service name for DNS resolution
# https://stackoverflow.com/a/54968946/10364409
CELERY_BROKER_URL = 'redis://redis:6379',
CELERY_RESULT_BACKEND = 'redis://redis:6379'


def make_celery(app_name=__name__):
    celery = Celery(
        app_name,
        backend=CELERY_RESULT_BACKEND,
        broker=CELERY_BROKER_URL
    )
    return celery


celery = make_celery()
