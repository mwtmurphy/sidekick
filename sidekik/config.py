'''configs for development and production'''
import datetime
import dotenv
from os import environ


#load environment varaibles
dotenv.load_dotenv()


class Config():
    '''Main configuration'''
    #app/form security
    SECRET_KEY = environ.get("SECRET_KEY") or "lorumipsumlorumipsumlorumipsum"

    #cookies
    REMEMBER_COOKIE_DURATION = datetime.timedelta(weeks=1)

    #db parameters
    SQLALCHEMY_DATABASE_URI = environ.get("DATABASE_URL") or "postgresql+psycopg2:///sidekik"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    #logging
    LOG_TO_STDOUT = environ.get("LOG_TO_STDOUT") or None

    #mail (tbd whether to use)
    MAIL_DEFAULT_SENDER = environ.get("MAIL_DEFAULT_SENDER")
    MAIL_SERVER = environ.get("MAIL_SERVER")
    MAIL_PORT = int(environ.get("MAIL_PORT") or 25)
    MAIL_USE_TLS = environ.get("MAIL_USE_TLS") is not None
    MAIL_USERNAME = environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = environ.get("MAIL_PASSWORD")
    ADMINS = ["hi@mwtmurphy.com"]


class TestConfig(Config):
    '''Unit testing configuration'''
    SQLALCHEMY_DATABASE_URI = "sqlite:///{temp_dpath}/app.db"
    TESTING = True
    WTF_CSRF_ENABLED = False
