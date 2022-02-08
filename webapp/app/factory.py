from flask import Flask
import os
from .celery_utils import init_celery
from . import create_app

PKG_NAME = os.path.dirname(os.path.relpath(__file__)).split("/")[-1]


def create_app_celery(config_name=PKG_NAME, **kwargs):
    app = create_app(config_name)
    if kwargs.get("celery"):
        init_celery(kwargs.get("celery"), app)
    from app.main import main
    app.register_blueprint(main)
    return app
