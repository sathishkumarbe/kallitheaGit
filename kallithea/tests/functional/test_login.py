# -*- coding: utf-8 -*-
from __future__ import with_statement
import re

import mock
from kallithea.tests import *
from kallithea.tests.fixture import Fixture
from kallithea.lib.utils2 import generate_api_key
from kallithea.lib.auth import check_password
from kallithea.lib import helpers as h
from kallithea.model.api_key import ApiKeyModel
from kallithea.model import validators
from kallithea.model.db import User, Notification
from kallithea.model.meta import Session

fixture = Fixture()


class TestLoginController(TestController):
    def setUp(self):
        self.remove_all_notifications()
        self.assertEqual(Notification.query().all(), [])

    def test_index(self):
        response = self.app.get(url(controller='login', action='index'))
        self.assertEqual(response.status, '200 OK')
        # Test response...

    def test_login_admin_ok(self):
        response = self.app.post(url(controller='login', action='index'),
                                 {'username': TEST_USER_ADMIN_LOGIN,
                                  'password': TEST_USER_ADMIN_PASS})
        self.assertEqual(response.status, '302 Found')
        self.assert_authenticated_user(response, TEST_USER_ADMIN_LOGIN)

        response = response.follow()
        response.mustcontain('/%s' % HG_REPO)

    def test_login_regular_ok(self):
        response = self.app.post(url(controller='login', action='index'),
                                 {'username': TEST_USER_REGULAR_LOGIN,
                                  'password': TEST_USER_REGULAR_PASS})

        self.assertEqual(response.status, '302 Found')
        self.assert_authenticated_user(response, TEST_USER_REGULAR_LOGIN)

        response = response.follow()
        response.mustcontain('/%s' % HG_REPO)

    def test_login_ok_came_from(self):
        test_came_from = '/_admin/users'
        response = self.app.post(url(controller='login', action='index',
                                     came_from=test_came_from),
                                 {'username': TEST_USER_ADMIN_LOGIN,
                                  'password': TEST_USER_ADMIN_PASS})
        self.assertEqual(response.status, '302 Found')
        response = response.follow()

        self.assertEqual(response.status, '200 OK')
        response.mustcontain('Users Administration')

    def test_login_do_not_remember(self):
        response = self.app.post(url(controller='login', action='index'),
                                 {'username': TEST_USER_REGULAR_LOGIN,
                                  'password': TEST_USER_REGULAR_PASS,
                                  'remember': False})

        self.assertIn('Set-Cookie', response.headers)
        for cookie in response.headers.getall('Set-Cookie'):
            self.assertFalse(re.search(r';\s+(Max-Age|Expires)=', cookie, re.IGNORECASE),
                'Cookie %r has expiration date, but should be a session cookie' % cookie)

    def test_login_remember(self):
        response = self.app.post(url(controller='login', action='index'),
                                 {'username': TEST_USER_REGULAR_LOGIN,
                                  'password': TEST_USER_REGULAR_PASS,
                                  'remember': True})

        self.assertIn('Set-Cookie', response.headers)
        for cookie in response.headers.getall('Set-Cookie'):
            self.assertTrue(re.search(r';\s+(Max-Age|Expires)=', cookie, re.IGNORECASE),
                'Cookie %r should have expiration date, but is a session cookie' % cookie)

    def test_logout(self):
        response = self.app.post(url(controller='login', action='index'),
                                 {'username': TEST_USER_REGULAR_LOGIN,
                                  'password': TEST_USER_REGULAR_PASS})

        # Verify that a login session has been established.
        response = self.app.get(url(controller='login', action='index'))
        response = response.follow()
        self.assertIn('authuser', response.session)

        response.click('Log Out')

        # Verify that the login session has been terminated.
        response = self.app.get(url(controller='login', action='index'))
        self.assertNotIn('authuser', response.session)

    @parameterized.expand([
          ('data:text/html,<script>window.alert("xss")</script>',),
          ('mailto:test@example.com',),
          ('file:///etc/passwd',),
          ('ftp://some.ftp.server',),
          ('http://other.domain/bl%C3%A5b%C3%A6rgr%C3%B8d',),
    ])
    def test_login_bad_came_froms(self, url_came_from):
        response = self.app.post(url(controller='login', action='index',
                                     came_from=url_came_from),
                                 {'username': TEST_USER_ADMIN_LOGIN,
                                  'password': TEST_USER_ADMIN_PASS})
        self.assertEqual(response.status, '302 Found')
        self.assertEqual(response._environ['paste.testing_variables']
                         ['tmpl_context'].came_from, '/')
        response = response.follow()

        self.assertEqual(response.status, '200 OK')

    def test_login_short_password(self):
        response = self.app.post(url(controller='login', action='index'),
                                 {'username': TEST_USER_ADMIN_LOGIN,
                                  'password': 'as'})
        self.assertEqual(response.status, '200 OK')

        response.mustcontain('Enter 3 characters or more')

    def test_login_wrong_username_password(self):
        response = self.app.post(url(controller='login', action='index'),
                                 {'username': 'error',
                                  'password': 'test12'})

        response.mustcontain('Invalid username')
        response.mustcontain('Invalid password')

    # verify that get arguments are correctly passed along login redirection

    @parameterized.expand([
        ({'foo':'one', 'bar':'two'}, ('foo=one', 'bar=two')),
        ({'blue': u'blå'.encode('utf-8'), 'green':u'grøn'},
             ('blue=bl%C3%A5', 'green=gr%C3%B8n')),
    ])
    def test_redirection_to_login_form_preserves_get_args(self, args, args_encoded):
        with fixture.anon_access(False):
            response = self.app.get(url(controller='summary', action='index',
                                        repo_name=HG_REPO,
                                        **args))
            self.assertEqual(response.status, '302 Found')
            for encoded in args_encoded:
                self.assertIn(encoded, response.location)

    @parameterized.expand([
        ({'foo':'one', 'bar':'two'}, ('foo=one', 'bar=two')),
        ({'blue': u'blå'.encode('utf-8'), 'green':u'grøn'},
             ('blue=bl%C3%A5', 'green=gr%C3%B8n')),
    ])
    def test_login_form_preserves_get_args(self, args, args_encoded):
        response = self.app.get(url(controller='login', action='index',
                                    came_from = '/_admin/users',
                                    **args))
        for encoded in args_encoded:
            self.assertIn(encoded, response.form.action)

    @parameterized.expand([
        ({'foo':'one', 'bar':'two'}, ('foo=one', 'bar=two')),
        ({'blue': u'blå'.encode('utf-8'), 'green':u'grøn'},
             ('blue=bl%C3%A5', 'green=gr%C3%B8n')),
    ])
    def test_redirection_after_successful_login_preserves_get_args(self, args, args_encoded):
        response = self.app.post(url(controller='login', action='index',
                                     came_from = '/_admin/users',
                                     **args),
                                 {'username': TEST_USER_ADMIN_LOGIN,
                                  'password': TEST_USER_ADMIN_PASS})
        self.assertEqual(response.status, '302 Found')
        for encoded in args_encoded:
            self.assertIn(encoded, response.location)

    @parameterized.expand([
        ({'foo':'one', 'bar':'two'}, ('foo=one', 'bar=two')),
        ({'blue': u'blå'.encode('utf-8'), 'green':u'grøn'},
             ('blue=bl%C3%A5', 'green=gr%C3%B8n')),
    ])
    def test_login_form_after_incorrect_login_preserves_get_args(self, args, args_encoded):
        response = self.app.post(url(controller='login', action='index',
                                     came_from = '/_admin/users',
                                     **args),
                                 {'username': 'error',
                                  'password': 'test12'})

        response.mustcontain('Invalid username')
        response.mustcontain('Invalid password')
        for encoded in args_encoded:
            self.assertIn(encoded, response.form.action)

    #==========================================================================
    # REGISTRATIONS
    #==========================================================================
    def test_register(self):
        response = self.app.get(url(controller='login', action='register'))
        response.mustcontain('Sign Up')

    def test_register_err_same_username(self):
        uname = TEST_USER_ADMIN_LOGIN
        response = self.app.post(url(controller='login', action='register'),
                                            {'username': uname,
                                             'password': 'test12',
                                             'password_confirmation': 'test12',
                                             'email': 'goodmail@domain.com',
                                             'firstname': 'test',
                                             'lastname': 'test'})

        msg = validators.ValidUsername()._messages['username_exists']
        msg = h.html_escape(msg % {'username': uname})
        response.mustcontain(msg)

    def test_register_err_same_email(self):
        response = self.app.post(url(controller='login', action='register'),
                                            {'username': 'test_admin_0',
                                             'password': 'test12',
                                             'password_confirmation': 'test12',
                                             'email': TEST_USER_ADMIN_EMAIL,
                                             'firstname': 'test',
                                             'lastname': 'test'})

        msg = validators.UniqSystemEmail()()._messages['email_taken']
        response.mustcontain(msg)

    def test_register_err_same_email_case_sensitive(self):
        response = self.app.post(url(controller='login', action='register'),
                                            {'username': 'test_admin_1',
                                             'password': 'test12',
                                             'password_confirmation': 'test12',
                                             'email': TEST_USER_ADMIN_EMAIL.title(),
                                             'firstname': 'test',
                                             'lastname': 'test'})
        msg = validators.UniqSystemEmail()()._messages['email_taken']
        response.mustcontain(msg)

    def test_register_err_wrong_data(self):
        response = self.app.post(url(controller='login', action='register'),
                                            {'username': 'xs',
                                             'password': 'test',
                                             'password_confirmation': 'test',
                                             'email': 'goodmailm',
                                             'firstname': 'test',
                                             'lastname': 'test'})
        self.assertEqual(response.status, '200 OK')
        response.mustcontain('An email address must contain a single @')
        response.mustcontain('Enter a value 6 characters long or more')

    def test_register_err_username(self):
        response = self.app.post(url(controller='login', action='register'),
                                            {'username': 'error user',
                                             'password': 'test12',
                                             'password_confirmation': 'test12',
                                             'email': 'goodmailm',
                                             'firstname': 'test',
                                             'lastname': 'test'})

        response.mustcontain('An email address must contain a single @')
        response.mustcontain('Username may only contain '
                'alphanumeric characters underscores, '
                'periods or dashes and must begin with an '
                'alphanumeric character')

    def test_register_err_case_sensitive(self):
        usr = TEST_USER_ADMIN_LOGIN.title()
        response = self.app.post(url(controller='login', action='register'),
                                            {'username': usr,
                                             'password': 'test12',
                                             'password_confirmation': 'test12',
                                             'email': 'goodmailm',
                                             'firstname': 'test',
                                             'lastname': 'test'})

        response.mustcontain('An email address must contain a single @')
        msg = validators.ValidUsername()._messages['username_exists']
        msg = h.html_escape(msg % {'username': usr})
        response.mustcontain(msg)

    def test_register_special_chars(self):
        response = self.app.post(url(controller='login', action='register'),
                                        {'username': 'xxxaxn',
                                         'password': 'ąćźżąśśśś',
                                         'password_confirmation': 'ąćźżąśśśś',
                                         'email': 'goodmailm@test.plx',
                                         'firstname': 'test',
                                         'lastname': 'test'})

        msg = validators.ValidPassword()._messages['invalid_password']
        response.mustcontain(msg)

    def test_register_password_mismatch(self):
        response = self.app.post(url(controller='login', action='register'),
                                            {'username': 'xs',
                                             'password': '123qwe',
                                             'password_confirmation': 'qwe123',
                                             'email': 'goodmailm@test.plxa',
                                             'firstname': 'test',
                                             'lastname': 'test'})
        msg = validators.ValidPasswordsMatch('password', 'password_confirmation')._messages['password_mismatch']
        response.mustcontain(msg)

    def test_register_ok(self):
        username = 'test_regular4'
        password = 'qweqwe'
        email = 'username@test.com'
        name = 'testname'
        lastname = 'testlastname'

        response = self.app.post(url(controller='login', action='register'),
                                            {'username': username,
                                             'password': password,
                                             'password_confirmation': password,
                                             'email': email,
                                             'firstname': name,
                                             'lastname': lastname,
                                             'admin': True})  # This should be overriden
        self.assertEqual(response.status, '302 Found')
        self.checkSessionFlash(response, 'You have successfully registered into Kallithea')

        ret = Session().query(User).filter(User.username == 'test_regular4').one()
        self.assertEqual(ret.username, username)
        self.assertEqual(check_password(password, ret.password), True)
        self.assertEqual(ret.email, email)
        self.assertEqual(ret.name, name)
        self.assertEqual(ret.lastname, lastname)
        self.assertNotEqual(ret.api_key, None)
        self.assertEqual(ret.admin, False)

    def test_forgot_password_wrong_mail(self):
        bad_email = 'username%wrongmail.org'
        response = self.app.post(
                        url(controller='login', action='password_reset'),
                            {'email': bad_email, }
        )

        response.mustcontain('An email address must contain a single @')

    def test_forgot_password(self):
        response = self.app.get(url(controller='login',
                                    action='password_reset'))
        self.assertEqual(response.status, '200 OK')

        username = 'test_password_reset_1'
        password = 'qweqwe'
        email = 'username@python-works.com'
        name = 'passwd'
        lastname = 'reset'

        new = User()
        new.username = username
        new.password = password
        new.email = email
        new.name = name
        new.lastname = lastname
        new.api_key = generate_api_key()
        Session().add(new)
        Session().commit()

        response = self.app.post(url(controller='login',
                                     action='password_reset'),
                                 {'email': email, })

        self.checkSessionFlash(response, 'Your password reset link was sent')

        response = response.follow()

        # BAD KEY

        key = "bad"
        response = self.app.get(url(controller='login',
                                    action='password_reset_confirmation',
                                    key=key))
        self.assertEqual(response.status, '302 Found')
        self.assertTrue(response.location.endswith(url('reset_password')))

        # GOOD KEY

        key = User.get_by_username(username).api_key
        response = self.app.get(url(controller='login',
                                    action='password_reset_confirmation',
                                    key=key))
        self.assertEqual(response.status, '302 Found')
        self.assertTrue(response.location.endswith(url('login_home')))

        self.checkSessionFlash(response,
                               ('Your password reset was successful, '
                                'new password has been sent to your email'))

        response = response.follow()

    def _get_api_whitelist(self, values=None):
        config = {'api_access_controllers_whitelist': values or []}
        return config

    @parameterized.expand([
        ('none', None),
        ('empty_string', ''),
        ('fake_number', '123456'),
        ('proper_api_key', None)
    ])
    def test_access_not_whitelisted_page_via_api_key(self, test_name, api_key):
        whitelist = self._get_api_whitelist([])
        with mock.patch('kallithea.CONFIG', whitelist):
            self.assertEqual([],
                             whitelist['api_access_controllers_whitelist'])
            if test_name == 'proper_api_key':
                #use builtin if api_key is None
                api_key = User.get_first_admin().api_key

            with fixture.anon_access(False):
                self.app.get(url(controller='changeset',
                                 action='changeset_raw',
                                 repo_name=HG_REPO, revision='tip', api_key=api_key),
                             status=403)

    @parameterized.expand([
        ('none', None, 302),
        ('empty_string', '', 302),
        ('fake_number', '123456', 302),
        ('fake_not_alnum', 'a-z', 302),
        ('fake_api_key', '0123456789abcdef0123456789ABCDEF01234567', 302),
        ('proper_api_key', None, 200)
    ])
    def test_access_whitelisted_page_via_api_key(self, test_name, api_key, code):
        whitelist = self._get_api_whitelist(['ChangesetController:changeset_raw'])
        with mock.patch('kallithea.CONFIG', whitelist):
            self.assertEqual(['ChangesetController:changeset_raw'],
                             whitelist['api_access_controllers_whitelist'])
            if test_name == 'proper_api_key':
                api_key = User.get_first_admin().api_key

            with fixture.anon_access(False):
                self.app.get(url(controller='changeset',
                                 action='changeset_raw',
                                 repo_name=HG_REPO, revision='tip', api_key=api_key),
                             status=code)

    def test_access_page_via_extra_api_key(self):
        whitelist = self._get_api_whitelist(['ChangesetController:changeset_raw'])
        with mock.patch('kallithea.CONFIG', whitelist):
            self.assertEqual(['ChangesetController:changeset_raw'],
                             whitelist['api_access_controllers_whitelist'])

            new_api_key = ApiKeyModel().create(TEST_USER_ADMIN_LOGIN, u'test')
            Session().commit()
            with fixture.anon_access(False):
                self.app.get(url(controller='changeset',
                                 action='changeset_raw',
                                 repo_name=HG_REPO, revision='tip', api_key=new_api_key.api_key),
                             status=200)

    def test_access_page_via_expired_api_key(self):
        whitelist = self._get_api_whitelist(['ChangesetController:changeset_raw'])
        with mock.patch('kallithea.CONFIG', whitelist):
            self.assertEqual(['ChangesetController:changeset_raw'],
                             whitelist['api_access_controllers_whitelist'])

            new_api_key = ApiKeyModel().create(TEST_USER_ADMIN_LOGIN, u'test')
            Session().commit()
            #patch the API key and make it expired
            new_api_key.expires = 0
            Session().add(new_api_key)
            Session().commit()
            with fixture.anon_access(False):
                self.app.get(url(controller='changeset',
                                 action='changeset_raw',
                                 repo_name=HG_REPO, revision='tip',
                                 api_key=new_api_key.api_key),
                             status=302)
