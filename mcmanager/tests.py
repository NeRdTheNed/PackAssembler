import unittest

from pyramid import testing
from pyramid import httpexceptions

from webob.multidict import MultiDict

from .schema import *


# Helper functions
def matchrequest(params=None, **kwargs):
    return testing.DummyRequest(matchdict=kwargs, params=params)


class GeneralViewTests(unittest.TestCase):

    """ Tests for more static views, don't contact db. """

    def setUp(self):
        self.config = testing.setUp()
        self.config.include('mcmanager.main')

    def tearDown(self):
        testing.tearDown()

    def makeOne(self, request):
        """ Creates a Views instance using the request. """
        from .views.general import GeneralViews

        return GeneralViews(request)

    @property
    def dummy(self):
        """ Returns a Views instance with a dummy request. """
        return self.makeOne(testing.DummyRequest())

    def test_home_view(self):
        """ Tests the home view, should have the title home. """
        result = self.dummy.home()
        self.assertEqual(result['title'], 'Home')

    def test_error_view(self):
        """ Error view should return correct message for an error type. """
        request = matchrequest(type='already_cloned')
        result = self.makeOne(request).error()
        self.assertIn('already cloned this pack', result['message'])


# DB helper functions
def create_user(group):
    return User(username='testuser', password=b'0',
                email='test@example.com', group=group).save()


def create_mod(owner, name='TestMod', author='SomeAuthor', url='http://someurl.com/'):
    return Mod(
        name=name,
        rid=name.replace(' ', '_'),
        author=author,
        url=url,
        owner=owner
    )


class DBTests(unittest.TestCase):

    def setUp(self):
        self.config = testing.setUp()
        self.config.add_route('modlist', '/mod/list')

    def tearDown(self):
        testing.tearDown()

    @classmethod
    def setUpClass(self):
        self.contributor = create_user('contributor')

    def makeOne(self, request):
        """ Returns an object. Should be overwritten. """
        return object()

    @property
    def dummy(self):
        """ Returns a Views instance with a dummy request. """
        return self.makeOne(testing.DummyRequest())


class ModViewTests(DBTests):

    def tearDown(self):
        super().tearDown()
        Mod.drop_collection()

    def makeOne(self, request):
        """ Create a Views instance using the request. """
        from .views.mods import ModViews

        return ModViews(request)

    def test_mod_list_view_with_no_mods(self):
        """ Ensure the modlist returns no mods. """
        result = self.dummy.modlist()
        self.assertFalse(result['mods'])

    def test_mod_list_view_with_mods(self):
        """ Ensure the modlist returns mods when they exist. """
        # Create dummy mods
        mod = create_mod(self.contributor, name='aMod').save()
        mod2 = create_mod(self.contributor, name='bMod').save()
        # Get result
        result = self.dummy.modlist()
        # Make sure the names are the same as the ones in the result list
        self.assertEqual(result['mods'][0].name, mod.name)
        self.assertEqual(result['mods'][1].name, mod2.name)

    def test_mod_list_view_with_mods_and_search(self):
        """
        Ensure the modlist returns only matching mods when
        a query is given.
        """
        # Create dummy mods
        create_mod(self.contributor, name='aMod').save()
        mod = create_mod(self.contributor, name='bMod').save()
        # Get result
        result = self.makeOne(
            testing.DummyRequest(params={'q': 'b'})).modlist()
        # Make sure there is only one mod
        self.assertTrue(len(result['mods']) == 1)
        self.assertEqual(result['mods'][0].name, mod.name)

    def test_mod_view_object(self):
        """ Ensure the mod view returns the correct mod object. """
        # Create dummy mod
        mod = create_mod(self.contributor).save()
        # Get result
        result = self.makeOne(matchrequest(id=mod.id)).viewmod()
        # Make sure there is information which matches with the mod in the page
        self.assertEqual(mod.name, result['mod'].name)
        self.assertEqual(mod.author, result['mod'].author)
        self.assertEqual(mod.url, result['mod'].url)

    def test_add_mod_view_with_bad_input(self):
        """ Ensure the add mod page is validated by inputting bad info. """
        # Create request
        request = testing.DummyRequest(params=MultiDict({
            'author': r'\%%HGWwws&@',
            'homepage': 'somehomepage'
            }))
        # Get result and make sure it's not HTTPFound
        try:
            #result = self.makeOne(request).addmod()
            self.makeOne(request).addmod()
        except httpexceptions.HTTPFound:
            self.fail('Bad input was accepted.')
