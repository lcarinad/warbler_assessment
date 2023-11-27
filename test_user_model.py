"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

        
    def tearDown(self):
        db.session.rollback()
    
    def test_user_model(self):
        """Does basic model work?"""
        u1 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u1)
        db.session.commit()
        
        # User should have no messages & no followers
        self.assertEqual(len(u1.messages), 0)
        self.assertEqual(len(u1.followers), 0)

    def test_repr_method(self):
        """Does string representation of user match the __repr__ method"""
        u1 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u1)
        db.session.commit()
        
        user_repr=repr(u1)
        expected_repr=f"<User #{u1.id}: {u1.username}, {u1.email}>"
        self.assertEqual(user_repr, expected_repr)

    def test_isfollowing(self):
        "Does isfollowing work as expected"

        u1 = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u1)
        db.session.commit()
        
        u2 = User(
            email="test2@test.com",
            username="testuser2",
            password="HASHED_PASSWORD2"
        )
        db.session.add(u2)
        db.session.commit()
        
        #u1 is not following u2
        self.assertFalse(u1.is_following(u2))

        #add u1 as a follower of u2
        u1.following.append(u2)
        db.session.commit()
        self.assertEqual(len(u1.following), 1)

        #now, u1 should be following u2
        self.assertTrue(u1.is_following(u2))

        self.assertTrue(u2.is_followed_by(u1))
        self.assertFalse(u1.is_followed_by(u2))
    
    def test_signup(self):
        # Test if User.signup successfully creates a new user given valid credentials
        new_user = User.signup(
            email="test3@test.com",
            username="testuser3",
            password="TestPwd",
            image_url="/static/images/default-pic.png")
        

        db.session.add(new_user)
        db.session.commit()

        # Check if the new user is correctly stored in the database
        self.assertIsNotNone(new_user.id)
        self.assertEqual(new_user.email, "test3@test.com")
        self.assertEqual(new_user.username, "testuser3")
        self.assertEqual(new_user.image_url, "/static/images/default-pic.png")

        # Test if User.authenticate successfully returns a user when given valid username and password
        authenticate_user=User.authenticate('testuser3', 'TestPwd')
        self.assertEqual(new_user, authenticate_user)

        # Test if User.authenticate fails to return a user when the username is invalid
        self.assertFalse(User.authenticate('nottestuser3', 'TestPwd'))
        
        # Test if User.authenticate fails to return a user when the password is invalid
        self.assertFalse(User.authenticate('testuser3', 'NotTestPwd'))