'''contributor and administration views'''

import email_validator
import flask
from flask import current_app, request
import flask_admin
from flask_admin import base
from flask_admin.contrib import sqla
import flask_login
from flask_login import current_user
import inflect
import pandas as pd
import time
from werkzeug import urls
import wtforms
from wtforms import validators

from sidekik import db, forms, models
from sidekik.models import CreatedWarmup, User, MoveType, Warmup, Workout


class AccountView(sqla.ModelView):
    '''view for user accounts'''
    column_default_sort = ("email")
    column_list = ("email", "roles")
    column_exclude_list = ("password")
    form_columns = ("email", "password1", "password2", "roles", "active")
    form_excluded_columns = ('password')
    form_extra_fields = {
        "password1": wtforms.PasswordField("Password", 
            description=("Passwords must be a minimum of 8 characters including a number, a "
                         "lowercase letter and uppercase letter."),
            validators=[validators.DataRequired()]
        ),
        "password2": wtforms.PasswordField("Confirm Password", validators=[validators.DataRequired()])
    }

    def is_accessible(self):
        if current_user.is_anonymous:
            return False
        else:
            return (current_user.is_authenticated and current_user.is_active and 
                    current_user.has_role(["Superuser"]))

    def inaccessible_callback(self, name, **kwargs):
        flask.flash("You need a superuser role to access this page")
        return flask.redirect(flask.url_for('admin.index'))

    def on_model_change(self, form, user, is_created):

        try:
            valid = email_validator.validate_email(form.email.data)
            user.email = valid.email
        except email_validator.EmailNotValidError:
            raise validators.ValidationError("The email provided is an invalid format")

        if form.password1.data == form.password2.data:
            if is_valid_password(form.password1.data):
                user.set_password(form.password1.data)
                db.session.add(user)
                db.session.commit()
            else:
                raise validators.ValidationError("The password provided is an invalid format")
        else:
            raise validators.ValidationError("The passwords provided do not match")


class CreatedWarmupsView(sqla.ModelView):
    '''view for created warmups'''
    can_create = False
    can_delete = False
    can_edit = False
    can_view_details = True
    column_default_sort = ("date")
    column_details_list = ("date", "ex_time", "workouts", "warmups", "passed")
    column_labels = {"date": "Date Created", "ex_time": "Time to Create (Seconds)", 
                     "n_workouts": "Workout Movements Selected", "n_warmups": "Warm-up Movements Suggested",
                     "warmups": "Warm-up Movements", "workouts": "Workout Movements"}
    column_list = ("date", "ex_time", "n_workouts", "n_warmups", "passed")
    
    def is_accessible(self):
        if current_user.is_anonymous:
            return False
        else:
            return (current_user.is_authenticated and current_user.is_active and 
                    current_user.has_role(["Contributor", "Superuser"]))

    def inaccessible_callback(self, name, **kwargs):
        flask.flash("You need a contributor role to access this page")
        return flask.redirect(flask.url_for('admin.index'))


class IndexView(flask_admin.AdminIndexView):
    '''Override of standard index view to force login'''
    @flask_admin.expose('/')
    def index(self):
        if current_user.is_anonymous:
            return flask.redirect(flask.url_for("admin.login"))
        
        #create percentages for amount of movements labelled by category (warm-up, workout)
        lab_warm_moves = [row.is_labelled for row in Warmup.query.all()]
        lab_warm_perc = round(100*sum(lab_warm_moves)/len(lab_warm_moves), 2) if len(lab_warm_moves) else 0

        lab_work_moves = [row.is_labelled for row in Workout.query.all()]
        lab_work_perc = round(100*sum(lab_work_moves)/len(lab_work_moves), 2) if len(lab_work_moves) else 0

        n_warmups = CreatedWarmup.query.count()

        return self.render("admin/index.html", n_warmups=n_warmups, lab_work_perc=lab_work_perc,
                           lab_warm_perc=lab_warm_perc)

    @flask_admin.expose('/login', methods=["GET", "POST"])
    def login(self):
        form = forms.LoginForm()

        if form.validate_on_submit():
            user = User.query.filter_by(email=form.email.data).first()

            if not user or not user.check_password(form.password.data):
                flask.flash("Invalid email or password")
                return flask.redirect(flask.url_for("admin.login"))

            flask_login.login_user(user, remember=form.remember_me.data)
            next_page = request.args.get("next")

            if not next_page or urls.url_parse(next_page).netloc != "":
                next_page = flask.url_for("admin.index")

            return flask.redirect(next_page)

        return self.render("admin/login.html", form=form, title="Login")

    @flask_admin.expose('/logout')
    @flask_login.login_required
    def logout(self):
        flask_login.logout_user()
        return flask.redirect(flask.url_for("movements.index"))


class MoveTypeView(sqla.ModelView):
    '''view for workout movements'''
    column_default_sort = ("name")
    column_list = ("name", "description")
    
    def is_accessible(self):
        if current_user.is_anonymous:
            return False
        else:
            return (current_user.is_authenticated and current_user.is_active and 
                    current_user.has_role(["Contributor", "Superuser"]))

    def inaccessible_callback(self, name, **kwargs):
        flask.flash("You need a contributor role to access this page")
        return flask.redirect(flask.url_for('admin.index'))


class RoleView(sqla.ModelView):
    '''view for user roles'''
    column_default_sort = ("name")
    column_list = ("name", "description")
    

    def is_accessible(self):
        if current_user.is_anonymous:
            return False
        else:
            return (current_user.is_authenticated and current_user.is_active and 
                    current_user.has_role(["Superuser"]))

    def inaccessible_callback(self, name, **kwargs):
        flask.flash("You need a superuser role to access this page")
        return flask.redirect(flask.url_for('admin.index'))


class UploadMoveCatView(flask_admin.BaseView):
    @flask_admin.expose("/", methods=["GET", "POST"])
    def index(self):

        form = forms.UploadMoveCatForm()

        if form.validate_on_submit():
            inf_eng = inflect.engine()
            form.df["Movement"] = form.df["Movement"].apply(models.parse_movement, inf_eng=inf_eng)

            ix_updated = []
            for move_model in [Warmup, Workout]:
                move_rows = move_model.query.filter(move_model.name.in_(form.df["Movement"])).all()
                for row in move_rows:
                    df_row = form.df[form.df["Movement"] == row.name]

                    for type_name in df_row.iloc[0][df_row.iloc[0] == 1].index:
                        move_type = MoveType.query.filter_by(name=type_name).first()

                        if move_type not in row.move_types:
                            row.move_types.append(move_type)
                    
                    db.session.add(row)
                    ix_updated.append(df_row.index[0])
            
            db.session.commit()
            flask.flash("Movement descriptions uploaded")
        
        move_types = sorted(MoveType.query.all(), key=lambda row: row.name)

        return self.render("admin/upload/categories.html", form=form, move_types=move_types)

    @flask_admin.expose("/movement_description.csv")
    def download(self):
        def generate_data():
            df = pd.DataFrame(sorted(set(
                [row.name for row in Workout.query.all() if len(row.move_types) == 0] + 
                [row.name for row in Warmup.query.all() if len(row.move_types) == 0]
            )), columns=["Movement"])

            df[sorted([row.name for row in MoveType.query.all()])] = ""

            print(df.head())

            #yield header
            yield ",".join(df.columns) + "\n"

            #yield data
            for _, row in df.iterrows():
                yield  ",".join(row) + "\n"
                    
        return flask.Response(flask.stream_with_context(generate_data()), mimetype='text/csv')

    def is_accessible(self):
        if current_user.is_anonymous:
            return False
        else:
            return (current_user.is_authenticated and current_user.is_active and 
                    current_user.has_role(["Contributor", "Superuser"]))

    def inaccessible_callback(self, name, **kwargs):
        flask.flash("You need a contributor role to access this page")
        return flask.redirect(flask.url_for('admin.index'))


class UploadMovesView(flask_admin.BaseView):
    @flask_admin.expose('/', methods=["GET", "POST"])
    def index(self):
        
        form = forms.UploadMovesForm()
        data = {}

        if form.validate_on_submit():
            inf_eng = inflect.engine()

            for work_move in form.df.columns:
                t_init = time.time()

                cl_work_move = models.parse_movement(work_move, inf_eng)
                work_row = Workout.query.filter_by(name=cl_work_move).first()

                if not work_row:
                    work_row = models.Workout(name=cl_work_move)

                for warm_move in form.df[work_move].dropna():
                    cl_warm_move = models.parse_movement(warm_move, inf_eng)
                    warm_row = Warmup.query.filter_by(name=cl_warm_move).first()
                
                    if not warm_row:
                        warm_row = models.Warmup(name=cl_warm_move)
                        db.session.add(warm_row)
                        db.session.commit()
                        
                    if warm_row not in work_row.warmups:
                        work_row.warmups.append(warm_row)

                work_row.warmups = sorted(work_row.warmups, key=lambda move: move.name)
                db.session.add(work_row)

                current_app.logger.info((f"[*] Movement: {cl_work_move}. Time to load: "
                                         f"{round(time.time() - t_init, 4)}"))

            db.session.commit()
            data["moves_uploaded"] = True

        return self.render("admin/upload/movements.html", form=form, data=data)

    def is_accessible(self):
        if current_user.is_anonymous:
            return False
        else:
            return (current_user.is_authenticated and current_user.is_active and 
                    current_user.has_role(["Contributor", "Superuser"]))

    def inaccessible_callback(self, name, **kwargs):
        flask.flash("You need a contributor role to access this page")
        return flask.redirect(flask.url_for('admin.index'))


class WarmupView(sqla.ModelView):
    '''view for warmup movements'''
    column_default_sort = ("name")
    column_labels = {"is_labelled": "Movement Labelled", "move_types": "Movement Types", 
                     "name": "Movement Name", "workouts": "Linked Workouts"}
    column_list = ("name", "is_labelled")
    form_columns = ("name", "move_types", "workouts")
    
    def is_accessible(self):
        if current_user.is_anonymous:
            return False
        else:
            return (current_user.is_authenticated and current_user.is_active and 
                    current_user.has_role(["Contributor", "Superuser"]))

    def inaccessible_callback(self, name, **kwargs):
        flask.flash("You need a contributor role to access this page")
        return flask.redirect(flask.url_for('admin.index'))


class WorkoutView(sqla.ModelView):
    '''view for workout movements'''
    column_default_sort = ("name")
    column_labels = {"is_labelled": "Movement Labelled", "move_types": "Movement Types", 
                     "name": "Movement Name", "warmups": "Linked Warm-ups"}
    column_list = ("name", "is_labelled")
    form_columns = ("name", "move_types", "warmups")
    
    def is_accessible(self):
        if current_user.is_anonymous:
            return False
        else:
            return (current_user.is_authenticated and current_user.is_active and 
                    current_user.has_role(["Contributor", "Superuser"]))

    def inaccessible_callback(self, name, **kwargs):
        flask.flash("You need a contributor role to access this page")
        return flask.redirect(flask.url_for('admin.index'))


#helper functions
def is_valid_password(phrase: str) -> bool:
    '''Returns True if phrase is 8 characters or more and has at least
    one numerical, upper case and lower case character. Else, returns 
    False'''
    password_valid = False

    if len(phrase) > 7:
        if any(el.isdigit() for el in phrase) and any(el.isupper() for el in phrase) and \
           any(el.islower() for el in phrase):
            password_valid = True

    return password_valid