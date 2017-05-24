import cherrypy
import unittest
import webtest
from cr.api.server import (app_setup,
                           validate_email,
                           validate_coordinates)
from cr.db.store import global_settings as settings, connect
from cr.db.loader import load_data

MONGO_DB_CONFIG  = {"url": "mongodb://localhost:27017/crunch_fitness_tests"}

class IntegrationTestCase(unittest.TestCase):
    def setUp(self):
        """ My solution for setting up a test environ.
        """
        settings.update(MONGO_DB_CONFIG)
        load_data(settings)
        app_setup(settings)
        cherrypy.config.update({'environment': 'embedded'})
        cherrypy.server.unsubscribe()
        cherrypy.engine.start()
        self.app = webtest.TestApp(cherrypy.tree)
        self.db = connect(settings)

    def tearDown(self):
        self.db.users.remove()
        cherrypy.engine.exit()

    def login_user(self):
        """ Helper method for authenticating """
        res = self.app.get('/login')
        form = res.form
        form['email'] = 'admin@crunch.io'
        form['password'] = '123456'
        res = form.submit('submit', status=302)
        return res

    def test_users_access(self):
        """ Ensure that only authenticated users can access /users """
        # webtest will fail if the wrong status is returned
        self.app.get('/users', status=401)

        # Authenticate
        self.login_user()

        # Fetch user data
        res = self.app.get('/users')
        self.assertEqual(res.content_type, 'application/json')

        # Logout
        res = self.app.get('/logout')
        form = res.form
        form.submit('submit', status=302)

        # Test access after logout
        self.app.get('/users', status=401)

    def test_users_creation(self):
        """ Test creation of new user """

        params = {"first_name": "The", "last_name": "Admin",
                  "registered": "Thursday, July 17, 2014 1:53 AM",
                  "longitude": "-32.081022", "latitude": "43.175753",
                  "company": "Crunch", "email": "admin2@crunch.io", "password": "abcde"}

        # No access to POST for anon
        self.app.post_json('/users', params=params, status=401)

        # Authenticate
        self.login_user()

        res = self.app.post_json('/users', params=params)
        self.assertEqual(res.json_body, {u'status': u'success'})

        # Check the DB for the record
        self.assertEqual(self.db.users.find({'email': 'admin2@crunch.io'}).count(), 1)

        # Posting with same email as existing user should be blocked
        res = self.app.post_json('/users', params=params, status=400)

        # Check the DB for the record
        self.assertEqual(self.db.users.find({'email': 'admin2@crunch.io'}).count(), 1)


class UnitTestCase(unittest.TestCase):

    def test_validate_email(self):
        """ Validate email addresses"""
        self.assertEqual(validate_email('a.b@bbc.co.uk'), True)
        self.assertEqual(validate_email('a.b@bbc.co.'), False)
        self.assertEqual(validate_email('a.b.com'), False)

    def test_validate_coordinates(self):
        """ Validate coordinates to ensure they are within range"""
        self.assertEqual(validate_coordinates(-123.443, -90), True)
        self.assertEqual(validate_coordinates(-181, 84), False)
        self.assertEqual(validate_coordinates(-180, -90.0), True)
        self.assertEqual(validate_coordinates(-180, -90.00000004), False)

if __name__ == '__main__':
    unittest.main()
