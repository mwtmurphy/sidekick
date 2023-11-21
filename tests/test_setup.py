'''Unit tests for production setup functions'''
import os
import shutil
import tempfile
import unittest

import sidekik
from sidekik import config, db, models
from sidekik.models import MoveType, Role, User


class TestProductionSetup(unittest.TestCase):
    '''test class for prooduction setup'''
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
    def test_create_admin(self):
        '''validates superuser and roles created when create_admin
        executed'''
        os.environ["SUPER_EMAIL"] = "dummy_user@email.com"
        os.environ["SUPER_PASSWORD"] = "DummyPassword123"

        with self.app_context:
            models.create_admin()
            inserted_user = User.query.first()
            inserted_roles = Role.query.all()

        self.assertEqual(inserted_user.email, "dummy_user@email.com")
        self.assertTrue(inserted_user.check_password("DummyPassword123"))
        self.assertEqual(["Superuser"], [row.name for row in inserted_user.roles])
        
        for role in inserted_roles:
            self.assertIn(role.name, ["Contributor", "Superuser"])

    def test_create_movement_types(self):
        '''validates all movement types added when create_movement_types
        executed'''
        with self.app_context:
            models.create_movement_types()
            inserted_types = sorted([row.name for row in MoveType.query.all()])
            
        expected_types = ["BPM", "Core", "Gait", "Hinge", "Lunge", "Pull", "Push", "Rotation", 
                          "Squat"]
        self.assertEqual(inserted_types, expected_types)


if __name__ == "__main__":
    unittest.main()
