import hashlib
import json
import re
import random
import sys
import cherrypy
from cr.db.store import global_settings as settings, connect


@cherrypy.tools.register('before_handler')
def check_access():
    """ Simple accces control tools"""
    if cherrypy.session.get('auth') is None:
        # FIXME Do we want to redirect to login here?
        raise cherrypy.HTTPError(401, 'Unauthorized')


def validate_data(longitude, latitude, email):
    """ Check to ensure that email, longitude and latitude are well-formed"""
    return validate_email(email) and validate_coordinates(longitude, latitude)


def validate_email(email):
    """ Validate email """
    valid_email = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
    if valid_email.search(email):
        return True
    return False


def validate_coordinates(longitude, latitude):
    """ Validate coordinates to ensure they are within range"""
    if abs(latitude) <= 90 and abs(longitude) <= 180:
        return True
    return False


class Root(object):

    def __init__(self, settings):
        self.db = connect(settings)

    @cherrypy.expose
    def index(self):
        return 'Welcome to Crunch.  Please <a href="/login">login</a>.'


@cherrypy.expose
class Logout(object):
    """
    Should log the user out, rendering them incapable of accessing the users endpoint, but
    """

    def GET(self):
        if cherrypy.session.get('auth') is None:
            raise cherrypy.HTTPRedirect('/login')

        return """
                <html>
                <head></head>
                <body>
                <h1> Logout </h1>
                <form method="post" action="/logout">
                <button type="submit">Log out</button>
                </form>
                </body>
                </html>
                """

    def POST(self):
        message = ''
        if cherrypy.session.get('auth'):
            cherrypy.lib.sessions.expire()
            cherrypy.session['auth'] = None
            message = 'You have logged out'
        raise cherrypy.HTTPRedirect('/login?message=%s' % message)


class DataConnection(object):
    """ Defines db connection for data classes. """

    def __init__(self, settings):
        self.db = connect(settings)


@cherrypy.expose
class Login(DataConnection):
    """
    a GET to this endpoint should provide the user login/logout capabilities

    a POST to this endpoint with credentials should set up persistence tokens for the user,
    allowing them to access other pages.

    hint: this is how the admin's password was generated:
            import hashlib; hashlib.sha1('123456').hexdigest()


    """
    def GET(self, message=None):
        if cherrypy.session.get('auth') is True:
            raise cherrypy.HTTPRedirect('/logout')

        return """
                <html>
                <head></head>
                <body>
                <h1> Login </h1>
                <h3>%s</h3>
                <form method="post" action="/login">
                <input type="text" name="email" />
                <input type="text" name="password" />
                <button type="submit">Login</button>
                </form>
                </body>
                </html>
                """ % message

    def POST(self, email, password):
        user = self.db.users.find_one({'email': email})
        if not user:
            message = 'No user with those credentials'
            raise cherrypy.HTTPRedirect('/login?message=%s' % message)
        if hashlib.sha1(password).hexdigest() == user['hash']:
            cherrypy.session['auth'] = True
            raise cherrypy.HTTPRedirect('/users')
        else:
            message = 'Your password is incorrect'
            raise cherrypy.HTTPRedirect('/login?message=%s' % message)


@cherrypy.expose
@cherrypy.tools.check_access()
class Distance(DataConnection):
    """ Returns min/max/average/std for distanced between users."""

    @cherrypy.tools.json_out()
    def GET(self):
        """
        Each user has a lat/lon associated with them.  Using only numpy, determine the distance
        between each user pair, and provide the min/max/average/std as a json response.
        This should be GET only.


        Don't code, but explain how would you scale this to 1,000,000 users, considering users
        changing position every few minutes?

        I do not see a way of returning the necessary values without recalculating the entire array.

        Other scaling considerations:
            1. Check to see if the values have changed.
            2. How much precision do you need? Can values below a certain threshold be defer the calculation?
            3. Use a cache for the user data. Updates to long/latitude update the db first. On
            success the cache data is update with key lookup and replacement. Goal is to reduce I/O
            latency and the expense of reading the entire table from the DB.

        """
        # I do not have enough experience with numpy to finish this portion in a reasonable amount of time.
        # As part of a team, this is a place where I would ask for guidance.
        return {'status': 'not implemented'}


@cherrypy.expose
@cherrypy.tools.check_access()
class Users(DataConnection):
    """ Setter and getter for user data."""

    @cherrypy.tools.json_out()
    def GET(self):
        """
        for GET: update this to return a json stream defining a listing of the users
        for POST: should add a new user to the users collection, with validation

        Only logged-in users should be able to connect.  If not logged in, should return the
        appropriate HTTP response.  Password information should not be revealed.

        note: Always return the appropriate response for the action requested.
        """
        # The original code does not set the correct header
        return {'users': [u for u in self.db.users.find()]}

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self):

        user_data = cherrypy.request.json
        try:
            longitude = float(user_data.get('longitude'))
            latitude = float(user_data.get('latitude'))
        except (TypeError, ValueError):
            raise cherrypy.HTTPError(400, '%s does not contain a valid coordinate pair' % user_data)

        try:
            email = user_data['email']
        except KeyError:
            raise cherrypy.HTTPError(400, 'No email address supplied')

        try:
            password = user_data['password']
        except KeyError:
            raise cherrypy.HTTPError(400, 'No password supplied')

        if not validate_data(longitude, latitude, email):
            raise cherrypy.HTTPError(400, '%s is not a valid post' % user_data)

        if self.db.users.find({'email': email}).count() > 0:
            raise cherrypy.HTTPError(400, 'There is an existing email user with the address %s' % email)

        try:
            user_data['hash'] = hashlib.sha1(password).hexdigest()
            # FIXME All '_id' are strings in the sample data, but MongoDB
            # inserts an ObjectId when '_id' is not specified.
            # This throws a serializable error.
            # For now we will simulate MonboDB's 12 byte ObjectID
            user_data['_id'] = "{0:x}".format(random.getrandbits(96))
            result = self.db.users.insert_one(user_data)
            if result.acknowledged:
                return {'status': 'success'}
            else:
                raise cherrypy.HTTPError(400, 'The record was not saved')

        except Exception as inst:
            raise cherrypy.HTTPError(500, 'An exception of type  %s occured' % type(inst))


def app_setup(db_settings):
    """ Setup the ENVIRONMENT LAYER"""
    settings.update(db_settings)
    cherrypy.config.update({'tools.sessions.on': True})

    cherrypy.tree.mount(
        Root(settings),
        '/'
    )
    cherrypy.tree.mount(
        Users(settings),
        '/users',
        config={'/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}}
    )
    cherrypy.tree.mount(
        Distance(settings),
        '/distance',
        config={'/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}}
    )
    cherrypy.tree.mount(
        Login(settings),
        '/login',
        config={'/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}}
    )
    cherrypy.tree.mount(
        Logout(),
        '/logout',
        config={'/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}}
    )


def run():
    app_setup(json.load(file(sys.argv[1])))
    cherrypy.quickstart()
