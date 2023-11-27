import os
from unittest import TestCase
from flask import session, g

from models import db, User, Message, Follows, Likes

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

app.app_context().push()

class UserViewsTestCase(TestCase):
    """Tests for view functions"""
    def setUp(self):
        """Add sample user"""
        db.drop_all()
        db.create_all()

        db.session.commit()

        self.client = app.test_client()

        self.testuser = User.signup(email="messagetest@test.com", username="testuser", password="HASHED_PASSWORD", image_url=None)
        self.testuser_id = 10000
        self.testuser.id = self.testuser_id
        self.u1 = User.signup("abc", "test1@test.com", "password", None)
        self.u1_id = 1000
        self.u1.id = self.u1_id
        self.u2=User.signup('def', "test2@test.com", "password", None)
        self.u2_id=2000
        self.u2.id=self.u2_id
        self.u3=User.signup('ghi', "test3@test.com", "password", None)
        self.u4=User.signup('testdoguser', "bones@test.com", "password", None)

        db.session.commit()

    def tearDown(self):
        """Clean up any fouled transaction"""
        response = super().tearDown()
        db.session.rollback()
        return response
    def testSignUp(self):
        """Test signup route"""
        #test user can succesfully view signup resource
        with self.client as client:
            response=client.get('/signup')
            html = response.text

            self.assertEqual(response.status_code, 200)
            self.assertIn('Join Warbler today.', html )
    
        #test user succesfully can sign up with valid credentials
        with self.client as client:
            response = client.post('/signup', data={'username':'testuser1', 'password':'abc123!', 'email':'testuser1@test.com'})

            html = response.text

            self.assertEqual(response.status_code, 200)
            self.assertIn("testuser1", html )
    
    def testLogin(self):
        """Test user is able to login"""
        #test user can view login page and html
        with self.client as client:
            response = client.get('/login')
            html = response.text

            self.assertEqual(response.status_code, 200)
            self.assertIn('Welcome back.', html)
        
    def testLoginSubmit(self):
        """Test user can login"""
        with self.client as client:
            response=client.post('/login', data={'username':'testuser', 'password':'HASHED_PASSWORD'}, follow_redirects=True)
            html = response.text

            self.assertEqual(response.status_code,200)
            self.assertIn('Welcome back.', html)
    def test_list_users(self):
        """Test list of users are on page"""
        with self.client as client:
            response = client.get('/users')
            html = response.text

            self.assertIn("@testuser", html)
            self.assertIn("@def", html)
            self.assertIn("@abc", html)
            self.assertIn("@ghi", html)
            self.assertIn("testdoguser", html)

    def test_users_search(self):
        with self.client as client:
            response = client.get("/users?q=test")
            html = response.text

            self.assertIn("@testuser", html)
            self.assertIn("@testdoguser", html)

            self.assertNotIn("@def", html)
            self.assertNotIn("@abc", html)
            self.assertNotIn("@ghi", html)
    
    def test_user_show(self):
        with self.client as client:
            response = client.get(f"/users/{self.u1_id}")
            html = response.text

            self.assertIn("@abc", html)
            self.assertEqual(response.status_code, 200)

    def setup_followers(self):
        f1 = Follows(user_being_followed_id = self.u1_id, user_following_id=self.testuser_id)
        f2 = Follows(user_being_followed_id = self.u2_id, user_following_id=self.testuser_id)
        f3= Follows(user_being_followed_id = self.testuser_id, user_following_id=self.u1_id)

        db.session.add_all([f1, f2, f3])
        db.session.commit()

    def test_user_show_with_follows(self):
        self.setup_followers()

        with self.client as client:
            response = client.get(f"/users/{self.testuser_id}")
            html = response.text
            #Test for count of 1 follower
            self.assertEqual(response.status_code, 200)
            self.assertIn('1', html)

            #Test for count on 0 likes
            self.assertIn('0', html)

            #Test for count on users following
            self.assertIn('2', html)

    def test_show_following(self):
        self.setup_followers()

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser_id

            response = client.get(f"/users/{self.testuser_id}/following")
            html = response.text
            self.assertIn('@def', html)
            self.assertIn('@abc', html)

            self.assertNotIn('@testdoguser', html)

    def test_show_followers(self):
        self.setup_followers()

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser_id
            response = client.get(f"/users/{self.testuser_id}/followers")
            html = response.text

            self.assertIn('@abc', html)
            self.assertNotIn('@testdoguser', html)

    def test_unauthorized_following_page_access(self):
        self.setup_followers()
        with self.client as client:
            response = client.get(f"/users/{self.testuser_id}/following", follow_redirects=True)
            html = response.text

            self.assertEqual(response.status_code, 200)
            self.assertNotIn("@abc", html)
            self.assertNotIn("@def", html)
            self.assertIn("Access unauthorized.", html)

    def test_unauthorized_follower_page_access(self):
        self.setup_followers()
        with self.client as client:
            response = client.get(f"/users/{self.testuser_id}/followers", follow_redirects=True)
            html = response.text

            self.assertEqual(response.status_code, 200)
            self.assertNotIn("@abc", html)
            self.assertIn("Access unauthorized.", html)
    
    def setup_likes(self):
        m1 = Message(text="This is a test message", user_id=self.testuser_id)
        m2 = Message(text="Coffee is great", user_id=self.testuser_id)
        m3 = Message(id=670, text="I love warble", user_id=self.u1_id)
        db.session.add_all([m1, m2, m3])
        db.session.commit()

        l1 = Likes(user_id=self.testuser_id, message_id=670)

        db.session.add(l1)
        db.session.commit()
    
    def test_user_show_with_likes(self):
        self.setup_likes()

        with self.client as client:
            response = client.get(f"/users/{self.testuser_id}")
            html = response.text
            self.assertEqual(response.status_code, 200)

            self.assertIn("@testuser", html)
            
            #test for 2 messages
            self.assertIn("2", html)
            
            #test for 1 like
            self.assertIn("1", html)

    def test_add_like(self):
        test_m=Message(text="My dogs are too cute!", user_id=self.u1_id, id=1987)
        db.session.add(test_m)
        db.session.commit()

        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser_id
            response = client.post(f"/users/add_like/1987", follow_redirects=True)

            self.assertEqual(response.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==1987).all()
            self.assertEqual(len(likes), 1) 
            self.assertEqual(likes[0].user_id, self.testuser_id)

    def test_remove_like(self):
        self.setup_likes()
        m=Message.query.filter(Message.text=="I love warble").one()
        self.assertIsNotNone(m)
        self.assertNotEqual(m.user_id, self.testuser_id)

        l = Likes.query.filter(Likes.user_id==self.testuser_id and Likes.message_id==m.id).one()

        self.assertIsNotNone(l)
        with self.client as client:
            with client.session_transaction() as session:
                session[CURR_USER_KEY] = self.testuser_id

            response = client.post(f"/users/delete_like/{m.id}", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            likes = Likes.query.filter(Likes.message_id==m.id).all()
            self.assertEqual(len(likes), 0) 

    def test_unauthorized_like(self):
        self.setup_likes()
        with self.client as client:
            response = client.get(f"/users/{self.testuser_id}/likes", follow_redirects=True)
            html = response.text

            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized.", html)



    

                                        
            
