"""
Unit tests for server etc
"""
import unittest
from flask import Flask
from YTSA_Core_Files.db import db
from YTSA_Core_Files.sql_models import Users
from YTSA_Core_Files.sql_admin_functions import validate_login
from YTSA_Core_Files.sql_admin_functions import sql_add_demo_data_random, sql_add_demo_data_testing
#import YTSA_Core_Files.sql_requests as sqrequests

class TestServerSuff(unittest.TestCase):
    """_summary_
        Some basic tests of server functionality
    """
    def set_up(self):
        """
        Create new db
        """
        # pylint: disable=attribute-defined-outside-init
        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///testing.db"
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()
            sql_add_demo_data_random(25)
            sql_add_demo_data_testing()
        return self.app

    def tear_down(self):
        """
        Destroy DB at end of test
        """
        # pylint: disable=attribute-defined-outside-init
        self.app = Flask(__name__)
        self.app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///testing.db"
        db.init_app(self.app)
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_login_valid(self):
        """_summary_
            Tests server for a valid login
        """
        self.tear_down()
        self.set_up()
        valid_user = db.session.execute(db.select(Users).filter_by(user_name='Admin')).scalar_one()
        valid_password = 'Admin'
        self.assertTrue(validate_login(valid_user, valid_password))
        self.tear_down()


if __name__ == '__main__':
    unittest.main()
