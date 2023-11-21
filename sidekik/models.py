'''postgres tables and their relationships'''
from datetime import datetime
import flask_login
import inflect
import pandas as pd
import pkg_resources
from os import environ
import time
import typing
from werkzeug import security

from sidekik import db, login


#tables
create_warm = db.Table("create_warm",
    db.Column("create_id", db.Integer, db.ForeignKey("created_warmup.id"), primary_key=True),
    db.Column("warm_id", db.Integer, db.ForeignKey("warmup.id"), primary_key=True)
)

create_work = db.Table("create_work",
    db.Column("create_id", db.Integer, db.ForeignKey("created_warmup.id"), primary_key=True),
    db.Column("work_id", db.Integer, db.ForeignKey("workout.id"), primary_key=True)
)

roles_users = db.Table("roles_users",
    db.Column("role_id", db.Integer, db.ForeignKey("role.id"), primary_key=True),
    db.Column("user_id", db.Integer, db.ForeignKey("user.id"), primary_key=True)
)

warm_types = db.Table("warm_types",
    db.Column("move_type_id", db.Integer, db.ForeignKey("move_type.id"), primary_key=True),
    db.Column("warm_id", db.Integer, db.ForeignKey("warmup.id"), primary_key=True)
)

warm_work = db.Table("warm_work",
    db.Column("warm_id", db.Integer, db.ForeignKey("warmup.id"), primary_key=True),
    db.Column("work_id", db.Integer, db.ForeignKey("workout.id"), primary_key=True)
)

work_types = db.Table("work_types",
    db.Column("move_type_id", db.Integer, db.ForeignKey("move_type.id"), primary_key=True),
    db.Column("work_id", db.Integer, db.ForeignKey("workout.id"), primary_key=True)
)


#models
class CreatedWarmup(db.Model):
    '''Class for tracking warm-ups created

    date datetime not_null
    ex_time_s float not_null
    workouts relationship
    warmups relationship
    '''

    id = db.Column(db.Integer(), primary_key=True)
    date = db.Column(db.DateTime, index=True, default=datetime.utcnow, nullable=False)
    ex_time = db.Column(db.Float)
    passed = db.Column(db.Boolean)
    warmups = db.relationship("Warmup", secondary=create_warm, lazy="subquery", 
                              backref=db.backref("created_warmups", lazy=True), order_by="Warmup.name")
    workouts = db.relationship("Workout", secondary=create_work, lazy="subquery", 
                               backref=db.backref("created_warmups", lazy=True), order_by="Workout.name")

    def __repr__(self):
        return f"<Warm-up Crated: {self.date}>"

    @property
    def n_workouts(self):
        '''Returns number of workout movements selected'''
        return len(self.workouts)

    @property
    def n_warmups(self):
        '''Returns number of warmup movements selected'''
        return len(self.warmups)

class MoveType(db.Model):
    '''Class for classifying movement type:

    name str(50) unique not_null
    description str(255) not_null
    '''

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Role: {self.name}>"

    def __str__(self):
        return self.name


class Role(db.Model):
    '''Class for user roles:
    
    name str(50) unique not_null
    description str(255) not_null
    users relationship
    '''

    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f"<Role: {self.name}>"

    def __str__(self):
        return self.name


class User(db.Model, flask_login.UserMixin):
    '''Class for contributor information:

    active bool not_null 
    email str(50) unique not_null
    password str not_null
    roles relationship
    '''

    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Boolean(), default=True, nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    roles = db.relationship("Role", secondary=roles_users, lazy="subquery", 
                            backref=db.backref("users", lazy=True), order_by="Role.name")

    @property
    def is_active(self):
        return self.active

    def __repr__(self):
        return f"<User: {self.email}>"

    def __str__(self):
        return self.email

    def check_password(self, password):
        return security.check_password_hash(self.password, password)

    def has_role(self, roles: list) -> bool:
        '''Returns true if user has role name in roles, else returns 
        false'''
        role_in = False
        for name in roles:
            if name in [row.name for row in self.roles]:
                role_in = True
                break

        return role_in

    def set_password(self, password):
        self.password = security.generate_password_hash(password)


class Warmup(db.Model):
    '''Class for warm-up movements, described by their attributes:
    
    name str(50) not_null
    workouts relationship
    '''

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), index=True, nullable=False, unique=True)
    move_types = db.relationship("MoveType", secondary=warm_types, lazy="subquery", 
                                 backref=db.backref("warmups", lazy=True), order_by="MoveType.name")


    def __repr__(self):
        return f"<Warm-up Movement: {self.name}>"

    def __str__(self):
        return self.name

    @property
    def is_labelled(self):
        return len(self.move_types) > 0


class Workout(db.Model):
    '''Class for workout movements, described by their attributes:

    name str(50) not_null
    warmups relationship
    '''

    id = db.Column(db.Integer, primary_key=True)
    move_types = db.relationship("MoveType", secondary=work_types, lazy="subquery", 
                                 backref=db.backref("workouts", lazy=True), order_by="MoveType.name")
    name = db.Column(db.String(50), index=True, nullable=False, unique=True)
    warmups = db.relationship("Warmup", secondary=warm_work, lazy="subquery", 
                              backref=db.backref("workouts", lazy=True), order_by="Warmup.name")

    def __repr__(self):
        return f"<Workout Movement: {self.name}>"
    
    def __str__(self):
        return self.name

    @property
    def is_labelled(self):
        return len(self.move_types) > 0

    @property
    def warmups_labelled(self):
        return any(item.is_labelled for item in self.warmups)



#login handler
@login.user_loader
def load_user(id):
    return User.query.get(int(id))


#helper functions
def create_admin(dev: bool = False) -> None:
    '''Inserts default admin with contributor and superuser roles into 
    db if they don't exist'''
    con_row = Role.query.filter_by(name="Contributor").first()
    if not con_row:
        con_row = Role(name="Contributor", description="Add, edit and delete movements")
        db.session.add(con_row)
        db.session.commit()

    sup_row = Role.query.filter_by(name="Superuser").first()
    if not sup_row:
        sup_row = Role(name="Superuser", description="Add, edit and delete users")
        db.session.add(sup_row)
        db.session.commit()

    if dev:
        if not User.query.filter_by(email="superuser@email.com").first():
            user = User(email="superuser@email.com", roles=[sup_row])
            user.set_password("DummyPass123")
            db.session.add(user)
            db.session.commit()
    else:
        if not User.query.filter_by(email=environ.get("SUPER_EMAIL")).first():
            user = User(email=environ.get("SUPER_EMAIL"), roles=[sup_row])
            user.set_password(environ.get("SUPER_PASSWORD"))
            db.session.add(user)
            db.session.commit()

def create_movement_types() -> None:
    '''Insert default movement types into db if movement type doesn't
    exist'''
    stream = pkg_resources.resource_stream(__name__, "data/movement_types.csv")
    df = pd.read_csv(stream)

    for _, row in df.iterrows():
        if not MoveType.query.filter_by(name=row["Name"]).first():
            type_row = MoveType(name=row["Name"], description=row["Description"])
            db.session.add(type_row)
    
    db.session.commit()
    stream.close()

def parse_movement(move: str, inf_eng) -> str:
    '''Returns parsed movement as singular noun in title format'''
    
    #convert sub-strings to title format if not an acronym
    split_move = move.split()
    for jx, word in enumerate(split_move):
        if not word.isupper():
            split_move[jx] = word.title()
        
    move = " ".join(split_move)
    
    #transform to singular noun unless ending in 'ss'
    if len(move) > 2:
        if move[-2:] != "ss" and move[-1] == "s":     
            sing_word = inf_eng.singular_noun(move)
            move = sing_word if sing_word else move
    
    return move
    