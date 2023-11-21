'''Unit tests for admin login'''
import shutil
import tempfile
import unittest

import sidekik
from sidekik import config, db, models


class TestLogin(unittest.TestCase):
    '''Test class for user login page and admin landing page'''
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

    def tearDown(self):
        with self.app_context:
            db.session.remove()
            db.drop_all()

    #unit tests
    def test_page_exists(self):
        '''Validates page exists'''
        response = self.test_client.get("/admin", follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_form_errors(self):
        '''Validates errors printed when fields aren't completed'''
        email = "dummy_user@email.com"
        phrase = "DummyPassword123"

        response = self.test_client.post("/admin/login", data={"email": email})
        self.assertIn(b"This field is required", response.data)

        response = self.test_client.post("/admin/login", data={"password": phrase})
        self.assertIn(b"This field is required", response.data)

    def test_successful_login(self):
        email = "dummy_user@email.com"
        phrase = "DummyPassword123"

        user = models.User(email=email)
        user.set_password(phrase)
        add_to_db(self.app_context, user)

        response = self.test_client.post("/admin/login", data={"email": email, "password": phrase},
                                         follow_redirects=True)
        self.assertIn(b"Warm-ups Created", response.data)

    def test_roles(self):
        '''validate roles provide you with respective tabs in admin home
        page'''
        email = "dummy_user@email.com"
        phrase = "DummyPassword123"

        user = models.User(email=email)
        user.set_password(phrase)
        add_to_db(self.app_context, user)

        self.test_client.post("/admin/login", data={"email": email, "password": phrase},
                              follow_redirects=True)

        response = self.test_client.get("/admin", follow_redirects=True)
        self.assertNotIn(b"Users", response.data)
        self.assertNotIn(b"Movements", response.data)
        self.assertNotIn(b"Upload", response.data)
        self.assertNotIn(b"Created Warm-ups", response.data)

        con_role = models.Role(name="Contributor", description="N/A")
        add_to_db(self.app_context, con_role)

        user.roles = [con_role]
        add_to_db(self.app_context, user)

        response = self.test_client.get("/admin", follow_redirects=True)
        self.assertNotIn(b"Users", response.data)
        self.assertIn(b"Movements", response.data)
        self.assertIn(b"Upload", response.data)
        self.assertIn(b"Created Warm-ups", response.data)

        sup_role = models.Role(name="Superuser", description="N/A")
        add_to_db(self.app_context, sup_role)

        user.roles = [sup_role]
        add_to_db(self.app_context, user)

        response = self.test_client.get("/admin", follow_redirects=True)
        self.assertIn(b"Users", response.data)
        self.assertIn(b"Movements", response.data)
        self.assertIn(b"Upload", response.data)
        self.assertIn(b"Created Warm-ups", response.data)        


def add_to_db(app_context, row) -> None:
    '''adds row to db and commits'''
    with app_context:
        db.session.add(row)
        db.session.commit()


if __name__ == "__main__":
    unittest.main()
