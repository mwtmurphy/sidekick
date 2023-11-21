'''Unit tests for main warm-up creation page'''
import bs4 
from os import path
import shutil
import tempfile
import unittest
from werkzeug import datastructures


import sidekik
from sidekik import config, db, models
from sidekik.models import Role, Warmup, Workout



class TestIndex(unittest.TestCase):
    '''test class for forgot password page'''
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
    def test_page_exists(self):
        '''validates page exists'''
        response = self.test_client.get("/", follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_warmup_suggestion(self):
        '''validates <= 3 movements suggested for 1 workout movement 
        provided, and > 3 mocements suggested for > 1 workout movement'''
        #add move types
        with self.app_context:
            models.create_movement_types()

        #add movements
        fpath = path.join(path.abspath(path.dirname(__file__)), "test_movements.csv")
        test_csv = datastructures.FileStorage(stream=open(fpath, "rb"), filename="test_movements.csv",
                                              content_type="text/csv")
        self.test_client.post("/admin/upload/movements/", data={"fmoves": test_csv}, 
                              content_type="multipart/form-data")

        #add movement categories
        desc_fpath = path.join(path.abspath(path.dirname(__file__)), "test_movement_description.csv")
        desc_csv = datastructures.FileStorage(stream=open(desc_fpath, "rb"), 
                                              filename="test_movement_description.csv", 
                                              content_type="text/csv")
        response = self.test_client.post("/admin/upload/categories/", data={"fmoves": desc_csv}, 
                                         content_type="multipart/form-data")
        self.assertIn(b"Movement descriptions uploaded", response.data)

        #test warm-up creation
        response = self.test_client.post("/", data={
            "moves-0-move": "Snatch"
        })
        soup = bs4.BeautifulSoup(response.data, "html.parser")
        list_items = [item for item in soup.div.ul.contents if item != "\n"]
        self.assertIn(len(list_items), list(range(1, 6)))


        response = self.test_client.post("/", data={
            "moves-0-move": "Power Snatch"
        })
        soup = bs4.BeautifulSoup(response.data, "html.parser")
        list_items = [item for item in soup.div.ul.contents if item != "\n"]
        self.assertIn(len(list_items), list(range(1, 6)))


        response = self.test_client.post("/", data={
            "moves-0-move": "Snatch",
            "moves-1-move": "Running"
        })
        soup = bs4.BeautifulSoup(response.data, "html.parser")
        list_items = [item for item in soup.div.ul.contents if item != "\n"]
        self.assertIn(len(list_items), list(range(1, 6)))



def add_to_db(app_context, row) -> None:
    '''adds row to db and commits'''
    with app_context:
        db.session.add(row)
        db.session.commit()


if __name__ == "__main__":
    unittest.main()
