'''app instantiation'''
import flask
import flask_admin
import flask_login
import flask_migrate
import flask_sqlalchemy
import logging

from sidekik import config


#extensions
admin_mgr = flask_admin.Admin(base_template="admin/base.html", template_mode="bootstrap4")
db = flask_sqlalchemy.SQLAlchemy()
login = flask_login.LoginManager()
login.login_view = "admin.login"
login.login_message = "Please sign in to see this page."
migrate = flask_migrate.Migrate()


def create_app(app_config=config.Config):
    #app creation and config
    app = flask.Flask(__name__)
    app.config.from_object(app_config)

    #add extensions
    from sidekik import views

    admin_mgr.init_app(app, index_view=views.IndexView())
    db.init_app(app)
    login.init_app(app)
    migrate.init_app(app, db)

     #load models
    from sidekik import models

    #register blueprints
    from sidekik import errors, movements

    app.register_blueprint(errors.bp)
    app.register_blueprint(movements.bp)
    app.add_url_rule("/", endpoint="index")

    #add admin views
    admin_mgr.add_view(views.AccountView(models.User, db.session, name="Accounts", category="Users"))
    admin_mgr.add_view(views.MoveTypeView(models.MoveType, db.session, name="Movement Types", 
                                        category="Movements"))
    admin_mgr.add_view(views.RoleView(models.Role, db.session, name="Roles", category="Users"))
    admin_mgr.add_view(views.UploadMoveCatView(name="Upload Movement Categories", 
                                               endpoint="upload/categories", category="Upload"))
    admin_mgr.add_view(views.UploadMovesView(name="Upload Movements", endpoint="upload/movements",
                                             category="Upload"))
    admin_mgr.add_view(views.WarmupView(models.Warmup, db.session, name="Warm-up Movements", 
                                        category="Movements"))
    admin_mgr.add_view(views.CreatedWarmupsView(models.CreatedWarmup, db.session, name="Created Warm-ups"))
    admin_mgr.add_view(views.WorkoutView(models.Workout, db.session, name="Workout Movements", 
                                         category="Movements"))
    #environment setup
    from sidekik.models import User

    if app.debug and not app.testing:
        #inserting example data
        @app.before_first_request
        def add_development_data():
            if not User.query.all():
                models.create_admin(dev=True)
                models.create_movement_types()

    elif not app.debug and not app.testing:
        #add initial user
        @app.before_first_request
        def add_initial_admin():
            if not User.query.all():
                models.create_admin()
                models.create_movement_types()

        #heroku logging
        if app.config['LOG_TO_STDOUT']:
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)

    return app
