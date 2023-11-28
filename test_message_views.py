"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
        self.testuser_id=10000
        self.testuser.id = self.testuser_id
        self.u1 = User.signup("abc", "test1@test.com", "password", None)
        self.u1_id = 1000
        self.u1.id = self.u1_id
        db.session.commit()
        self.message = Message(id=670, text="I love cheese!", user_id= self.u1_id)
        self.message1=Message(id=1987, text="Dogs are the best", user_id= self.u1_id)

        db.session.add_all([self.message, self.message1])
        db.session.commit()

    def tearDown(self):
        """Clean up any fouled transaction"""
        response = super().tearDown()
        db.session.rollback()

        return response
    
    def test_add_message(self):
        """Can user add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            resp = c.get('/messages/new')
            html = resp.text

            self.assertEqual(resp.status_code, 200)
            self.assertIn("happening?", html)


        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)

            html = resp.text
            self.assertEqual(resp.status_code, 200)

            self.assertIn("Hello", html)
    
    def test_unauthorized_add_message(self):
        """Test user can not add message if not signed in"""

        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            html = resp.text

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized.', html)
            self.assertNotIn('Hello', html)


    def test_show_message(self):
        """Check message renders"""
        with self.client as client:
            resp=client.get('/messages/670')
            html = resp.text

            self.assertEqual(resp.status_code, 200)
            self.assertIn('I love cheese!', html)

    def test_destroy_message(self):
        """Test message deletion"""

        with self.client as client:
            with client.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1.id
            resp=client.post('/messages/1987/delete', follow_redirects=True)
            html = resp.text

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn('Dogs are the best', html)
    
    def test_unauthorized_destroy_message(self):
        """Test user can not delete msg if not signed in"""
        with self.client as client:
            resp=client.post('/messages/1987/delete', follow_redirects=True)
            html = resp.text
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(resp.location, "/")



    
