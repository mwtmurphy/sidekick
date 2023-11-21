'''Unit tests for admin forms'''
from os import path
import shutil
import tempfile
import unittest
from werkzeug import datastructures


import sidekik
from sidekik import config, db, models
from sidekik.models import Role, Warmup, Workout

class TestAdminForms(unittest.TestCase):
    '''Test class for admin user forms'''
    #setup
    @classmethod
    def setUpClass(cls):
        cls.temp_dpath = tempfile.mkdtemp()
        cls.config = config.TestConfig
        cls.config.SQLALCHEMY_DATABASE_URI = cls.config.SQLALCHEMY_DATABASE_URI.format(
            temp_dpath=cls.temp_dpath
        )

        cls.app = sidekik.create_app(cls.config)
        cls.app_context = cls.app.app_context()
        cls.app_context.push()
        cls.test_client = cls.app.test_client()

    @classmethod
    def tearDownClass(cls):
        cls.app_context.pop()
        shutil.rmtree(cls.temp_dpath)

    def setUp(self):
        with self.app_context:
            db.create_all()

        sup_role = models.Role(name="Superuser", description="N/A")
        add_to_db(self.app_context, sup_role)
        
        self.email = "dummy_user@email.com"
        self.phrase = "DummyPassword123"
        
        user = models.User(email=self.email)
        user.set_password(self.phrase)
        user.roles = [sup_role]
        add_to_db(self.app_context, user)

        self.test_client.post("/admin/login", data={"email": self.email, "password": self.phrase})

    def tearDown(self):
        with self.app_context:
            db.session.remove()
            db.drop_all()

    #unit tests
    def test_create_user(self):
        '''validates user with valid email and password can be created'''
        new_email = "dummy_contributor@email.com"
        con_role = Role.query.filter_by(name="Contributor").first()

        self.test_client.post("/admin/user/new/?url=%2Fadmin%2Fuser%2F", data={
            "email": new_email, 
            "password1": self.phrase,
            "password2": self.phrase, 
            "roles": [con_role]
        })

        self.test_client.post("/admin/logout")
        response = self.test_client.post("/admin/login", data={
            "email": new_email, "password": self.phrase
        }, follow_redirects=True)
        self.assertIn(b"Warm-ups Created", response.data)

    def test_create_bad_user(self):
        '''validates errors thrown when invalid email and password 
        submitted'''
        bad_email = "notanemail"
        con_role = Role.query.filter_by(name="Contributor").first()

        response = self.test_client.post("/admin/user/new/?url=%2Fadmin%2Fuser%2F", data={
            "email": bad_email, 
            "password1": self.phrase,
            "password2": self.phrase, 
            "roles": [con_role]
        })
        self.assertIn(b"The email provided is an invalid format", response.data)

        good_email = "dummy_contributor@email.com"

        response = self.test_client.post("/admin/user/new/?url=%2Fadmin%2Fuser%2F", data={
            "email": good_email, 
            "password1": self.phrase,
            "password2": self.phrase + "bad", 
            "roles": [con_role]
        })
        self.assertIn(b"The passwords provided do not match", response.data)

        bad_phrase = "badpass"

        response = self.test_client.post("/admin/user/new/?url=%2Fadmin%2Fuser%2F", data={
            "email": good_email, 
            "password1": bad_phrase,
            "password2": bad_phrase, 
            "roles": [con_role]
        })
        self.assertIn(b"The password provided is an invalid format", response.data)

    def test_movements_upload(self):
        '''validates movements uploaded to respective tables when file
        is correct'''
        fpath = path.join(path.abspath(path.dirname(__file__)), "test_movements.csv")
        test_csv = datastructures.FileStorage(stream=open(fpath, "rb"), filename="test_movements.csv",
                                              content_type="text/csv")

        response = self.test_client.post("/admin/upload/movements/", data={"fmoves": test_csv}, 
                                         content_type="multipart/form-data")
        self.assertIn(b"Movements uploaded", response.data)

        work_names = sorted([row.name for row in Workout.query.all()])
        for move in ["Power Snatch", "Snatch"]:
            self.assertIn(move, work_names)

        warm_names = sorted([row.name for row in Warmup.query.all()])
        for move in ["Muscle Snatch", "Snatch Deadlift"]:
            self.assertIn(move, warm_names)

    def test_movement_description(self):
        '''validates movement descriptions updated when file is 
        correct'''
        with self.app_context:
            models.create_movement_types()

        move_fpath = path.join(path.abspath(path.dirname(__file__)), "test_movements.csv")
        move_csv = datastructures.FileStorage(stream=open(move_fpath, "rb"), 
                                              filename="test_movements.csv", 
                                              content_type="text/csv")
        self.test_client.post("/admin/upload/movements/", data={"fmoves": move_csv}, 
                              content_type="multipart/form-data")

        desc_fpath = path.join(path.abspath(path.dirname(__file__)), "test_movement_description.csv")
        desc_csv = datastructures.FileStorage(stream=open(desc_fpath, "rb"), 
                                              filename="test_movement_description.csv", 
                                              content_type="text/csv")
        response = self.test_client.post("/admin/upload/categories/", data={"fmoves": desc_csv}, 
                                         content_type="multipart/form-data")
        self.assertIn(b"Movement descriptions uploaded", response.data)

        warm_row = Warmup.query.filter_by(name="Overhead Squat").first()
        self.assertEqual(["Push", "Squat"], sorted(row.name for row in warm_row.move_types))
        
        work_row = Workout.query.filter_by(name="Snatch").first()
        self.assertEqual(["Hinge", "Pull", "Push", "Squat"], sorted(row.name for row in work_row.move_types))


def add_to_db(app_context, row) -> None:
    '''adds row to db and commits'''
    with app_context:
        db.session.add(row)
        db.session.commit()


if __name__ == "__main__":
    unittest.main()
