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


class MessageModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()
    
    def test_message_model(self):
        """Does basic model work?"""
        u1 = User(
            email="messagetest@test.com",
            username="testusermessage",
            password="HASHED_PASSWORD"
        )
        db.session.add(u1)
        db.session.commit()
  
        m1 = Message(
            text="This is a test message.",
            user_id=u1.id
        )

        db.session.add(m1)
        db.session.commit()

        self.assertEqual(len(u1.messages), 1)
        self.assertEqual(m1.text, 'This is a test message.')

        
    def test_user_deleted(self):
        """test if user is deleted, message is deleted"""
        u1 = User(email="messagetest@test.com",
            username="testusermessage",
            password="HASHED_PASSWORD")

        db.session.add(u1)
        db.session.commit()
        print(f"*********************{u1.id}")
        m1= Message( text="This is a test message.", 
                    user_id=u1.id)
       
        db.session.add(m1)
        db.session.commit()

        db.session.delete(u1)
        db.session.commit()
        self.assertNotIsInstance(m1, Message)


        

        
