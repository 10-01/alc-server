# -*- coding: utf-8 -*-

"""
    A real simple app for using webapp2 with auth and session.

    It just covers the basics. Creating a user, login, logout
    and a decorator for protecting certain handlers.

    Routes are setup in routes.py and added in main.py
"""
# standard library imports
import logging
import json

# related third party imports
import webapp2
import httpagentparser
from webapp2_extras import security
from webapp2_extras.auth import InvalidAuthIdError, InvalidPasswordError
from webapp2_extras.i18n import gettext as _
from webapp2_extras.appengine.auth.models import Unique
from google.appengine.api import taskqueue
from google.appengine.api import users
from google.appengine.api.datastore_errors import BadValueError
from google.appengine.runtime import apiproxy_errors
from google.appengine.ext import blobstore
from google.appengine.api import images
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import urlfetch
from external.github import github
from external.linkedin import linkedin

# local application/library specific imports
from lib import utils, captcha, twitter
from lib.basehandler import BaseHandler
from lib.decorators import user_required
from lib.decorators import taskqueue_method
from lib import facebook
from web import forms as forms, models

import lib.cloudstorage as gcs


from lib.basehandler import BaseHandler
from lib.decorators import user_required



class SecureRequestHandler(BaseHandler):
    """
    Only accessible to users that are logged in
    """

    @user_required
    def get(self, **kwargs):
        user_session = self.user
        user_session_object = self.auth.store.get_session(self.request)

        user_info = models.User.get_by_id(long( self.user_id ))
        user_info_object = self.auth.store.user_model.get_by_auth_token(
            user_session['user_id'], user_session['token'])

        try:
            params = {
                "user_session" : user_session,
                "user_session_object" : user_session_object,
                "user_info" : user_info,
                "user_info_object" : user_info_object,
                "userinfo_logout-url" : self.auth_config['logout_url'],
                }
            return self.render_template('secure_zone.html', **params)
        except (AttributeError, KeyError), e:
            return "Secure zone error:" + " %s." % e



class LoginRequiredHandler(BaseHandler):
    def get(self):
        continue_url, = self.request.get('continue', allow_multiple=True)
        self.redirect(users.create_login_url(dest_url=continue_url))


class RegisterBaseHandler(BaseHandler):
    """
    Base class for handlers with registration and login forms.
    """

    @webapp2.cached_property
    def form(self):
        return forms.RegisterForm(self)


class SendEmailHandler(BaseHandler):
    """
    Core Handler for sending Emails
    Use with TaskQueue
    """

    @taskqueue_method
    def post(self):

        from google.appengine.api import mail, app_identity

        to = self.request.get("to")
        subject = self.request.get("subject")
        body = self.request.get("body")
        sender = self.request.get("sender")

        if sender != '' or not utils.is_email_valid(sender):
            if utils.is_email_valid(self.app.config.get('contact_sender')):
                sender = self.app.config.get('contact_sender')
            else:
                app_id = app_identity.get_application_id()
                sender = "%s <no-reply@%s.appspotmail.com>" % (app_id, app_id)

        if self.app.config['log_email']:
            try:
                logEmail = models.LogEmail(
                    sender=sender,
                    to=to,
                    subject=subject,
                    body=body,
                    when=utils.get_date_time("datetimeProperty")
                )
                logEmail.put()
            except (apiproxy_errors.OverQuotaError, BadValueError):
                logging.error("Error saving Email Log in datastore")

        try:
            message = mail.EmailMessage()
            message.sender = sender
            message.to = to
            message.subject = subject
            message.html = body
            message.send()
        except Exception, e:
            logging.error("Error sending email: %s" % e)


class LoginHandler(BaseHandler):
    """
    Handler for authentication
    """

    def get(self):
        """ Returns a simple HTML form for login """

        if self.user:
            self.redirect_to('home')
        params = {}
        return self.render_template('login.html', **params)

    def post(self):
        """
        username: Get the username from POST dict
        password: Get the password from POST dict
        """

        if not self.form.validate():
            return self.get()
        username = self.form.username.data.lower()
        continue_url = self.request.get('continue_url').encode('ascii', 'ignore')

        try:
            if utils.is_email_valid(username):
                user = models.User.get_by_email(username)
                if user:
                    auth_id = user.auth_ids[0]
                else:
                    raise InvalidAuthIdError
            else:
                auth_id = "own:%s" % username
                user = models.User.get_by_auth_id(auth_id)

            password = self.form.password.data.strip()
            remember_me = True if str(self.request.POST.get('remember_me')) == 'on' else False

            # Password to SHA512
            password = utils.hashing(password, self.app.config.get('salt'))

            # Try to login user with password
            # Raises InvalidAuthIdError if user is not found
            # Raises InvalidPasswordError if provided password
            # doesn't match with specified user
            self.auth.get_user_by_password(
                auth_id, password, remember=remember_me)

            # if user account is not activated, logout and redirect to home
            if (user.activated == False):
                # logout
                self.auth.unset_session()

                # redirect to home with error message
                resend_email_uri = self.uri_for('resend-account-activation', user_id=user.get_id(),
                                                token=models.User.create_resend_token(user.get_id()))
                message = _('Your account has not yet been activated. Please check your email to activate it or') + \
                          ' <a href="' + resend_email_uri + '">' + _('click here') + '</a> ' + _('to resend the email.')
                self.add_message(message, 'error')
                return self.redirect_to('home')

            # check twitter association in session
            twitter_helper = twitter.TwitterAuth(self)
            twitter_association_data = twitter_helper.get_association_data()
            if twitter_association_data is not None:
                if models.SocialUser.check_unique(user.key, 'twitter', str(twitter_association_data['id'])):
                    social_user = models.SocialUser(
                        user=user.key,
                        provider='twitter',
                        uid=str(twitter_association_data['id']),
                        extra_data=twitter_association_data
                    )
                    social_user.put()

            # check facebook association
            fb_data = None
            try:
                fb_data = json.loads(self.session['facebook'])
            except:
                pass

            if fb_data is not None:
                if models.SocialUser.check_unique(user.key, 'facebook', str(fb_data['id'])):
                    social_user = models.SocialUser(
                        user=user.key,
                        provider='facebook',
                        uid=str(fb_data['id']),
                        extra_data=fb_data
                    )
                    social_user.put()

            # check linkedin association
            li_data = None
            try:
                li_data = json.loads(self.session['linkedin'])
            except:
                pass

            if li_data is not None:
                if models.SocialUser.check_unique(user.key, 'linkedin', str(li_data['id'])):
                    social_user = models.SocialUser(
                        user=user.key,
                        provider='linkedin',
                        uid=str(li_data['id']),
                        extra_data=li_data
                    )
                    social_user.put()

            # end linkedin

            if self.app.config['log_visit']:
                try:
                    logVisit = models.LogVisit(
                        user=user.key,
                        uastring=self.request.user_agent,
                        ip=self.request.remote_addr,
                        timestamp=utils.get_date_time()
                    )
                    logVisit.put()
                except (apiproxy_errors.OverQuotaError, BadValueError):
                    logging.error("Error saving Visit Log in datastore")
            if continue_url:
                self.redirect(continue_url)
            else:
                self.redirect_to('home')
        except (InvalidAuthIdError, InvalidPasswordError), e:
            # Returns error message to self.response.write in
            # the BaseHandler.dispatcher
            message = _("Your username or password is incorrect. "
                        "Please try again (make sure your caps lock is off)")
            self.add_message(message, 'error')
            self.redirect_to('login', continue_url=continue_url) if continue_url else self.redirect_to('login')

    @webapp2.cached_property
    def form(self):
        return forms.LoginForm(self)


class SocialLoginHandler(BaseHandler):
    """
    Handler for Social authentication
    """

    def get(self, provider_name):
        provider = self.provider_info[provider_name]

        if not self.app.config.get('enable_federated_login'):
            message = _('Federated login is disabled.')
            self.add_message(message, 'warning')
            return self.redirect_to('login')
        callback_url = "%s/social_login/%s/complete" % (self.request.host_url, provider_name)

        if provider_name == "twitter":
            twitter_helper = twitter.TwitterAuth(self, redirect_uri=callback_url)
            self.redirect(twitter_helper.auth_url())

        elif provider_name == "facebook":
            self.session['linkedin'] = None
            perms = ['email', 'publish_stream']
            self.redirect(facebook.auth_url(self.app.config.get('fb_api_key'), callback_url, perms))

        elif provider_name == 'linkedin':
            self.session['facebook'] = None
            authentication = linkedin.LinkedInAuthentication(
                self.app.config.get('linkedin_api'),
                self.app.config.get('linkedin_secret'),
                callback_url,
                [linkedin.PERMISSIONS.BASIC_PROFILE, linkedin.PERMISSIONS.EMAIL_ADDRESS])
            self.redirect(authentication.authorization_url)

        elif provider_name == "github":
            scope = 'gist'
            github_helper = github.GithubAuth(self.app.config.get('github_server'),
                                              self.app.config.get('github_client_id'), \
                                              self.app.config.get('github_client_secret'),
                                              self.app.config.get('github_redirect_uri'), scope)
            self.redirect(github_helper.get_authorize_url())

        elif provider_name in models.SocialUser.open_id_providers():
            continue_url = self.request.get('continue_url')
            if continue_url:
                dest_url = self.uri_for('social-login-complete', provider_name=provider_name, continue_url=continue_url)
            else:
                dest_url = self.uri_for('social-login-complete', provider_name=provider_name)
            try:
                login_url = users.create_login_url(federated_identity=provider['uri'], dest_url=dest_url)
                self.redirect(login_url)
            except users.NotAllowedError:
                self.add_message('You must enable Federated Login Before for this application.<br> '
                                 '<a href="http://appengine.google.com" target="_blank">Google App Engine Control Panel</a> -> '
                                 'Administration -> Application Settings -> Authentication Options', 'error')
                self.redirect_to('login')

        else:
            message = _('%s authentication is not yet implemented.' % provider.get('label'))
            self.add_message(message, 'warning')
            self.redirect_to('login')


class CallbackSocialLoginHandler(BaseHandler):
    """
    Callback (Save Information) for Social Authentication
    """

    def get(self, provider_name):
        if not self.app.config.get('enable_federated_login'):
            message = _('Federated login is disabled.')
            self.add_message(message, 'warning')
            return self.redirect_to('login')
        continue_url = self.request.get('continue_url')
        if provider_name == "twitter":
            oauth_token = self.request.get('oauth_token')
            oauth_verifier = self.request.get('oauth_verifier')
            twitter_helper = twitter.TwitterAuth(self)
            user_data = twitter_helper.auth_complete(oauth_token,
                                                     oauth_verifier)
            logging.info('twitter user_data: ' + str(user_data))
            if self.user:
                # new association with twitter
                user_info = models.User.get_by_id(long(self.user_id))
                if models.SocialUser.check_unique(user_info.key, 'twitter', str(user_data['user_id'])):
                    social_user = models.SocialUser(
                        user=user_info.key,
                        provider='twitter',
                        uid=str(user_data['user_id']),
                        extra_data=user_data
                    )
                    social_user.put()

                    message = _('Twitter association added.')
                    self.add_message(message, 'success')
                else:
                    message = _('This Twitter account is already in use.')
                    self.add_message(message, 'error')
                if continue_url:
                    self.redirect(continue_url)
                else:
                    self.redirect_to('edit-profile')
            else:
                # login with twitter
                social_user = models.SocialUser.get_by_provider_and_uid('twitter',
                                                                        str(user_data['user_id']))
                if social_user:
                    # Social user exists. Need authenticate related site account
                    user = social_user.user.get()
                    self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
                    if self.app.config['log_visit']:
                        try:
                            logVisit = models.LogVisit(
                                user=user.key,
                                uastring=self.request.user_agent,
                                ip=self.request.remote_addr,
                                timestamp=utils.get_date_time()
                            )
                            logVisit.put()
                        except (apiproxy_errors.OverQuotaError, BadValueError):
                            logging.error("Error saving Visit Log in datastore")
                    if continue_url:
                        self.redirect(continue_url)
                    else:
                        self.redirect_to('home')
                else:
                    uid = str(user_data['user_id'])
                    email = str(user_data.get('email'))
                    self.create_account_from_social_provider(provider_name, uid, email, continue_url, user_data)

        # github association
        elif provider_name == "github":
            # get our request code back from the social login handler above
            code = self.request.get('code')

            # create our github auth object
            scope = 'gist'
            github_helper = github.GithubAuth(self.app.config.get('github_server'),
                                              self.app.config.get('github_client_id'), \
                                              self.app.config.get('github_client_secret'),
                                              self.app.config.get('github_redirect_uri'), scope)

            # retrieve the access token using the code and auth object
            access_token = github_helper.get_access_token(code)
            user_data = github_helper.get_user_info(access_token)
            logging.info('github user_data: ' + str(user_data))
            if self.user:
                # user is already logged in so we set a new association with twitter
                user_info = models.User.get_by_id(long(self.user_id))
                if models.SocialUser.check_unique(user_info.key, 'github', str(user_data['login'])):
                    social_user = models.SocialUser(
                        user=user_info.key,
                        provider='github',
                        uid=str(user_data['login']),
                        extra_data=user_data
                    )
                    social_user.put()

                    message = _('Github association added.')
                    self.add_message(message, 'success')
                else:
                    message = _('This Github account is already in use.')
                    self.add_message(message, 'error')
                self.redirect_to('edit-profile')
            else:
                # user is not logged in, but is trying to log in via github
                social_user = models.SocialUser.get_by_provider_and_uid('github', str(user_data['login']))
                if social_user:
                    # Social user exists. Need authenticate related site account
                    user = social_user.user.get()
                    self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
                    if self.app.config['log_visit']:
                        try:
                            logVisit = models.LogVisit(
                                user=user.key,
                                uastring=self.request.user_agent,
                                ip=self.request.remote_addr,
                                timestamp=utils.get_date_time()
                            )
                            logVisit.put()
                        except (apiproxy_errors.OverQuotaError, BadValueError):
                            logging.error("Error saving Visit Log in datastore")
                    self.redirect_to('home')
                else:
                    uid = str(user_data['id'])
                    email = str(user_data.get('email'))
                    self.create_account_from_social_provider(provider_name, uid, email, continue_url, user_data)
        #end github

        # facebook association
        elif provider_name == "facebook":
            code = self.request.get('code')
            callback_url = "%s/social_login/%s/complete" % (self.request.host_url, provider_name)
            token = facebook.get_access_token_from_code(code, callback_url, self.app.config.get('fb_api_key'),
                                                        self.app.config.get('fb_secret'))
            access_token = token['access_token']
            fb = facebook.GraphAPI(access_token)
            user_data = fb.get_object('me')
            logging.info('facebook user_data: ' + str(user_data))
            if self.user:
                # new association with facebook
                user_info = models.User.get_by_id(long(self.user_id))
                if models.SocialUser.check_unique(user_info.key, 'facebook', str(user_data['id'])):
                    social_user = models.SocialUser(
                        user=user_info.key,
                        provider='facebook',
                        uid=str(user_data['id']),
                        extra_data=user_data
                    )
                    social_user.put()

                    message = _('Facebook association added!')
                    self.add_message(message, 'success')
                else:
                    message = _('This Facebook account is already in use!')
                    self.add_message(message, 'error')
                if continue_url:
                    self.redirect(continue_url)
                else:
                    self.redirect_to('edit-profile')
            else:
                # login with Facebook
                social_user = models.SocialUser.get_by_provider_and_uid('facebook',
                                                                        str(user_data['id']))
                if social_user:
                    # Social user exists. Need authenticate related site account
                    user = social_user.user.get()
                    self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
                    if self.app.config['log_visit']:
                        try:
                            logVisit = models.LogVisit(
                                user=user.key,
                                uastring=self.request.user_agent,
                                ip=self.request.remote_addr,
                                timestamp=utils.get_date_time()
                            )
                            logVisit.put()
                        except (apiproxy_errors.OverQuotaError, BadValueError):
                            logging.error("Error saving Visit Log in datastore")
                    if continue_url:
                        self.redirect(continue_url)
                    else:
                        self.redirect_to('home')
                else:
                    uid = str(user_data['id'])
                    email = str(user_data.get('email'))
                    self.create_account_from_social_provider(provider_name, uid, email, continue_url, user_data)

                    # end facebook
        # association with linkedin
        elif provider_name == "linkedin":
            callback_url = "%s/social_login/%s/complete" % (self.request.host_url, provider_name)
            authentication = linkedin.LinkedInAuthentication(
                self.app.config.get('linkedin_api'),
                self.app.config.get('linkedin_secret'),
                callback_url,
                [linkedin.PERMISSIONS.BASIC_PROFILE, linkedin.PERMISSIONS.EMAIL_ADDRESS])
            authentication.authorization_code = self.request.get('code')
            access_token = authentication.get_access_token()
            link = linkedin.LinkedInApplication(authentication)
            u_data = link.get_profile(selectors=['id', 'first-name', 'last-name', 'email-address'])
            user_data = {
                'first_name': u_data.get('firstName'),
                'last_name': u_data.get('lastName'),
                'id': u_data.get('id'),
                'email': u_data.get('emailAddress')}
            self.session['linkedin'] = json.dumps(user_data)
            logging.info('linkedin user_data: ' + str(user_data))

            if self.user:
                # new association with linkedin
                user_info = models.User.get_by_id(long(self.user_id))
                if models.SocialUser.check_unique(user_info.key, 'linkedin', str(user_data['id'])):
                    social_user = models.SocialUser(
                        user=user_info.key,
                        provider='linkedin',
                        uid=str(user_data['id']),
                        extra_data=user_data
                    )
                    social_user.put()

                    message = _('Linkedin association added!')
                    self.add_message(message, 'success')
                else:
                    message = _('This Linkedin account is already in use!')
                    self.add_message(message, 'error')
                if continue_url:
                    self.redirect(continue_url)
                else:
                    self.redirect_to('edit-profile')
            else:
                # login with Linkedin
                social_user = models.SocialUser.get_by_provider_and_uid('linkedin',
                                                                        str(user_data['id']))
                if social_user:
                    # Social user exists. Need authenticate related site account
                    user = social_user.user.get()
                    self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
                    if self.app.config['log_visit']:
                        try:
                            logVisit = models.LogVisit(
                                user=user.key,
                                uastring=self.request.user_agent,
                                ip=self.request.remote_addr,
                                timestamp=utils.get_date_time()
                            )
                            logVisit.put()
                        except (apiproxy_errors.OverQuotaError, BadValueError):
                            logging.error("Error saving Visit Log in datastore")
                    if continue_url:
                        self.redirect(continue_url)
                    else:
                        self.redirect_to('home')
                else:
                    uid = str(user_data['id'])
                    email = str(user_data.get('email'))
                    self.create_account_from_social_provider(provider_name, uid, email, continue_url, user_data)

                    #end linkedin

        # google, myopenid, yahoo OpenID Providers
        elif provider_name in models.SocialUser.open_id_providers():
            provider_display_name = models.SocialUser.PROVIDERS_INFO[provider_name]['label']
            # get info passed from OpenId Provider
            from google.appengine.api import users

            current_user = users.get_current_user()
            if current_user:
                if current_user.federated_identity():
                    uid = current_user.federated_identity()
                else:
                    uid = current_user.user_id()
                email = current_user.email()
            else:
                message = _('No user authentication information received from %s. '
                            'Please ensure you are logging in from an authorized OpenID Provider (OP).'
                            % provider_display_name)
                self.add_message(message, 'error')
                return self.redirect_to('login', continue_url=continue_url) if continue_url else self.redirect_to(
                    'login')
            if self.user:
                # add social account to user
                user_info = models.User.get_by_id(long(self.user_id))
                if models.SocialUser.check_unique(user_info.key, provider_name, uid):
                    social_user = models.SocialUser(
                        user=user_info.key,
                        provider=provider_name,
                        uid=uid
                    )
                    social_user.put()

                    message = _('%s association successfully added.' % provider_display_name)
                    self.add_message(message, 'success')
                else:
                    message = _('This %s account is already in use.' % provider_display_name)
                    self.add_message(message, 'error')
                if continue_url:
                    self.redirect(continue_url)
                else:
                    self.redirect_to('edit-profile')
            else:
                # login with OpenId Provider
                social_user = models.SocialUser.get_by_provider_and_uid(provider_name, uid)
                if social_user:
                    # Social user found. Authenticate the user
                    user = social_user.user.get()
                    self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
                    if self.app.config['log_visit']:
                        try:
                            logVisit = models.LogVisit(
                                user=user.key,
                                uastring=self.request.user_agent,
                                ip=self.request.remote_addr,
                                timestamp=utils.get_date_time()
                            )
                            logVisit.put()
                        except (apiproxy_errors.OverQuotaError, BadValueError):
                            logging.error("Error saving Visit Log in datastore")
                    if continue_url:
                        self.redirect(continue_url)
                    else:
                        self.redirect_to('home')
                else:
                    self.create_account_from_social_provider(provider_name, uid, email, continue_url)
        else:
            message = _('This authentication method is not yet implemented.')
            self.add_message(message, 'warning')
            self.redirect_to('login', continue_url=continue_url) if continue_url else self.redirect_to('login')

    def create_account_from_social_provider(self, provider_name, uid, email=None, continue_url=None, user_data=None):
        """Social user does not exist yet so create it with the federated identity provided (uid)
        and create prerequisite user and log the user account in
        """
        provider_display_name = models.SocialUser.PROVIDERS_INFO[provider_name]['label']
        if models.SocialUser.check_unique_uid(provider_name, uid):
            # create user
            # Returns a tuple, where first value is BOOL.
            # If True ok, If False no new user is created
            # Assume provider has already verified email address
            # if email is provided so set activated to True
            auth_id = "%s:%s" % (provider_name, uid)
            if email:
                unique_properties = ['email']
                user_info = self.auth.store.user_model.create_user(
                    auth_id, unique_properties, email=email,
                    activated=True
                )
            else:
                user_info = self.auth.store.user_model.create_user(
                    auth_id, activated=True
                )
            if not user_info[0]: #user is a tuple
                message = _('The account %s is already in use.' % provider_display_name)
                self.add_message(message, 'error')
                return self.redirect_to('register')

            user = user_info[1]

            # create social user and associate with user
            social_user = models.SocialUser(
                user=user.key,
                provider=provider_name,
                uid=uid,
                )
            if user_data:
                social_user.extra_data = user_data
                self.session[provider_name] = json.dumps(user_data) # TODO is this needed?
            social_user.put()
            # authenticate user
            self.auth.set_session(self.auth.store.user_to_dict(user), remember=True)
            if self.app.config['log_visit']:
                try:
                    logVisit = models.LogVisit(
                        user=user.key,
                        uastring=self.request.user_agent,
                        ip=self.request.remote_addr,
                        timestamp=utils.get_date_time()
                    )
                    logVisit.put()
                except (apiproxy_errors.OverQuotaError, BadValueError):
                    logging.error("Error saving Visit Log in datastore")

            message = _(
                'Welcome!  You have been registered as a new user through %s and logged in.' % provider_display_name)
            self.add_message(message, 'success')
        else:
            message = _('This %s account is already in use.' % provider_display_name)
            self.add_message(message, 'error')
        if continue_url:
            self.redirect(continue_url)
        else:
            self.redirect_to('edit-profile')


class DeleteSocialProviderHandler(BaseHandler):
    """
    Delete Social association with an account
    """

    @user_required
    def post(self, provider_name):
        if self.user:
            user_info = models.User.get_by_id(long(self.user_id))
            if len(user_info.get_social_providers_info()['used']) > 1 or (user_info.password is not None):
                social_user = models.SocialUser.get_by_user_and_provider(user_info.key, provider_name)
                if social_user:
                    social_user.key.delete()
                    message = _('%s successfully disassociated.' % provider_name)
                    self.add_message(message, 'success')
                else:
                    message = _('Social account on %s not found for this user.' % provider_name)
                    self.add_message(message, 'error')
            else:
                message = ('Social account on %s cannot be deleted for user.'
                           '  Please create a username and password to delete social account.' % provider_name)
                self.add_message(message, 'error')
        self.redirect_to('edit-profile')


class LogoutHandler(BaseHandler):
    """
    Destroy user session and redirect to login
    """

    def get(self):
        if self.user:
            message = _("You've signed out successfully. ")
            self.add_message(message, 'info')

        self.auth.unset_session()
        # User is logged out, let's try redirecting to login page
        try:
            self.redirect(self.auth_config['login_url'])
            return self.redirect_to('home')
        except (AttributeError, KeyError), e:
            logging.error("Error logging out: %s" % e)
            message = _("User is logged out, but there was an error on the redirection.")
            self.add_message(message, 'error')
            return self.redirect_to('home')


class RegisterHandler(BaseHandler):
    """
    Handler for Sign Up Users
    """

    def get(self):
        """ Returns a simple HTML form for create a new user """

        if self.user:
            self.redirect_to('home')
        params = {}
        return self.render_template('register.html', **params)

    def post(self):
        """ Get fields from POST dict """

        if not self.form.validate():
            return self.get()
        username = self.form.username.data.lower()
        name = self.form.name.data.strip()
        last_name = self.form.last_name.data.strip()
        email = self.form.email.data.lower()
        password = self.form.password.data.strip()
        country = self.form.country.data
        tz = self.form.tz.data

        # Password to SHA512
        password = utils.hashing(password, self.app.config.get('salt'))

        # Passing password_raw=password so password will be hashed
        # Returns a tuple, where first value is BOOL.
        # If True ok, If False no new user is created
        unique_properties = ['username', 'email']
        auth_id = "own:%s" % username
        user = self.auth.store.user_model.create_user(
            auth_id, unique_properties, password_raw=password,
            username=username, name=name, last_name=last_name, email=email,
            ip=self.request.remote_addr, country=country, tz=tz
        )

        if not user[0]: #user is a tuple
            if "username" in str(user[1]):
                message = _(
                    'Sorry, The username <strong>{}</strong> is already registered.').format(username)
            elif "email" in str(user[1]):
                message = _('Sorry, The email <strong>{}</strong> is already registered.').format(email)
            else:
                message = _('Sorry, The user is already registered.')
            self.add_message(message, 'error')
            return self.redirect_to('register')
        else:
            # User registered successfully
            add_apikey = models.ApiKeys(
                user_name = username,
                user_id = user[1].get_id(),
                role = "user"
            )
            add_apikey.put()

            # But if the user registered using the form, the user has to check their email to activate the account ???
            try:
                if not user[1].activated:
                    # send email
                    subject = _("%s Account Verification" % self.app.config.get('app_name'))
                    confirmation_url = self.uri_for("account-activation",
                                                    user_id=user[1].get_id(),
                                                    token=models.User.create_auth_token(user[1].get_id()),
                                                    _full=True)

                    # load email's template
                    template_val = {
                        "app_name": self.app.config.get('app_name'),
                        "username": username,
                        "confirmation_url": confirmation_url,
                        "support_url": self.uri_for("contact", _full=True)
                    }
                    body_path = "emails/account_activation.txt"
                    body = self.jinja2.render_template(body_path, **template_val)

                    email_url = self.uri_for('taskqueue-send-email')
                    taskqueue.add(url=email_url, params={
                        'to': str(email),
                        'subject': subject,
                        'body': body,
                        })

                    message = _('You were successfully registered. '
                                'Please check your email to activate your account.')
                    self.add_message(message, 'success')
                    return self.redirect_to('home')

                # If the user didn't register using registration form ???
                db_user = self.auth.get_user_by_password(user[1].auth_ids[0], password)

                # Check Twitter association in session
                twitter_helper = twitter.TwitterAuth(self)
                twitter_association_data = twitter_helper.get_association_data()
                if twitter_association_data is not None:
                    if models.SocialUser.check_unique(user[1].key, 'twitter', str(twitter_association_data['id'])):
                        social_user = models.SocialUser(
                            user=user[1].key,
                            provider='twitter',
                            uid=str(twitter_association_data['id']),
                            extra_data=twitter_association_data
                        )
                        social_user.put()

                #check Facebook association
                fb_data = json.loads(self.session['facebook'])
                if fb_data is not None:
                    if models.SocialUser.check_unique(user.key, 'facebook', str(fb_data['id'])):
                        social_user = models.SocialUser(
                            user=user.key,
                            provider='facebook',
                            uid=str(fb_data['id']),
                            extra_data=fb_data
                        )
                        social_user.put()

                #check LinkedIn association
                li_data = json.loads(self.session['linkedin'])
                if li_data is not None:
                    if models.SocialUser.check_unique(user.key, 'linkedin', str(li_data['id'])):
                        social_user = models.SocialUser(
                            user=user.key,
                            provider='linkedin',
                            uid=str(li_data['id']),
                            extra_data=li_data
                        )
                        social_user.put()

                message = _('Welcome <strong>{}</strong>, you are now logged in.').format(username)
                self.add_message(message, 'success')
                return self.redirect_to('home')
            except (AttributeError, KeyError), e:
                logging.error('Unexpected error creating the user %s: %s' % (username, e ))
                message = _('Unexpected error creating the user %s' % username)
                self.add_message(message, 'error')
                return self.redirect_to('home')

    @webapp2.cached_property
    def form(self):
        f = forms.RegisterForm(self)
        f.country.choices = self.countries_tuple
        f.tz.choices = self.tz
        return f


class AccountActivationHandler(BaseHandler):
    """
    Handler for account activation
    """

    def get(self, user_id, token):
        try:
            if not models.User.validate_auth_token(user_id, token):
                message = _('The link is invalid.')
                self.add_message(message, 'error')
                return self.redirect_to('home')

            user = models.User.get_by_id(long(user_id))
            # activate the user's account
            user.activated = True
            user.put()

            # Login User
            self.auth.get_user_by_token(int(user_id), token)

            # Delete token
            models.User.delete_auth_token(user_id, token)

            #Add user to Mailchimp list
            self.form_fields = {
                "email": user.email,
                "function": 'trial_add',
                "ip": user.ip
            }

            taskqueue.add(url='/mc', params=self.form_fields)

            message = _('Congratulations, Your account <strong>{}</strong> has been successfully activated.').format(
                user.username)
            self.add_message(message, 'success')
            self.redirect_to('home')

        except (AttributeError, KeyError, InvalidAuthIdError, NameError), e:
            logging.error("Error activating an account: %s" % e)
            message = _('Sorry, Some error occurred.')
            self.add_message(message, 'error')
            return self.redirect_to('home')


class ResendActivationEmailHandler(BaseHandler):
    """
    Handler to resend activation email
    """

    def get(self, user_id, token):
        try:
            if not models.User.validate_resend_token(user_id, token):
                message = _('The link is invalid.')
                self.add_message(message, 'error')
                return self.redirect_to('home')

            user = models.User.get_by_id(long(user_id))
            email = user.email

            if (user.activated == False):
                # send email
                subject = _("%s Account Verification" % self.app.config.get('app_name'))
                confirmation_url = self.uri_for("account-activation",
                                                user_id=user.get_id(),
                                                token=models.User.create_auth_token(user.get_id()),
                                                _full=True)

                # load email's template
                template_val = {
                    "app_name": self.app.config.get('app_name'),
                    "username": user.username,
                    "confirmation_url": confirmation_url,
                    "support_url": self.uri_for("contact", _full=True)
                }
                body_path = "emails/account_activation.txt"
                body = self.jinja2.render_template(body_path, **template_val)

                email_url = self.uri_for('taskqueue-send-email')
                taskqueue.add(url=email_url, params={
                    'to': str(email),
                    'subject': subject,
                    'body': body,
                    })

                models.User.delete_resend_token(user_id, token)

                message = _('The verification email has been resent to %s. '
                            'Please check your email to activate your account.' % email)
                self.add_message(message, 'success')
                return self.redirect_to('home')
            else:
                message = _('Your account has been activated. Please <a href="/login/">sign in</a> to your account.')
                self.add_message(message, 'warning')
                return self.redirect_to('home')

        except (KeyError, AttributeError), e:
            logging.error("Error resending activation email: %s" % e)
            message = _('Sorry, Some error occurred.')
            self.add_message(message, 'error')
            return self.redirect_to('home')


class ContactHandler(BaseHandler):
    """
    Handler for Contact Form
    """

    def get(self):
        """ Returns a simple HTML for contact form """

        if self.user:
            user_info = models.User.get_by_id(long(self.user_id))
            if user_info.name or user_info.last_name:
                self.form.name.data = user_info.name + " " + user_info.last_name
            if user_info.email:
                self.form.email.data = user_info.email
        params = {
            "exception": self.request.get('exception')
        }

        return self.render_template('contact.html', **params)

    def post(self):
        """ validate contact form """

        if not self.form.validate():
            return self.get()
        remoteip = self.request.remote_addr
        user_agent = self.request.user_agent
        exception = self.request.POST.get('exception')
        name = self.form.name.data.strip()
        email = self.form.email.data.lower()
        message = self.form.message.data.strip()

        try:
            # parsing user_agent and getting which os key to use
            # windows uses 'os' while other os use 'flavor'
            ua = httpagentparser.detect(user_agent)
            _os = ua.has_key('flavor') and 'flavor' or 'os'

            operating_system = str(ua[_os]['name']) if "name" in ua[_os] else "-"
            if 'version' in ua[_os]:
                operating_system += ' ' + str(ua[_os]['version'])
            if 'dist' in ua:
                operating_system += ' ' + str(ua['dist'])

            browser = str(ua['browser']['name']) if 'browser' in ua else "-"
            browser_version = str(ua['browser']['version']) if 'browser' in ua else "-"

            template_val = {
                "name": name,
                "email": email,
                "browser": browser,
                "browser_version": browser_version,
                "operating_system": operating_system,
                "ip": remoteip,
                "message": message
            }
        except Exception as e:
            logging.error("error getting user agent info: %s" % e)

        try:
            subject = _("Contact")
            # exceptions for error pages that redirect to contact
            if exception != "":
                subject = subject + " (Exception error: %s)" % exception

            body_path = "emails/contact.txt"
            body = self.jinja2.render_template(body_path, **template_val)

            email_url = self.uri_for('taskqueue-send-email')
            taskqueue.add(url=email_url, params={
                'to': self.app.config.get('contact_recipient'),
                'subject': subject,
                'body': body,
                'sender': self.app.config.get('contact_sender'),
                })

            message = _('Your message was sent successfully.')
            self.add_message(message, 'success')
            return self.redirect_to('contact')

        except (AttributeError, KeyError), e:
            logging.error('Error sending contact form: %s' % e)
            message = _('Error sending the message. Please try again later.')
            self.add_message(message, 'error')
            return self.redirect_to('contact')

    @webapp2.cached_property
    def form(self):
        return forms.ContactForm(self)


class EditProfileHandler(BaseHandler):
    """
    Handler for Edit User Profile
    """

    @user_required
    def get(self):
        """ Returns a simple HTML form for edit profile """

        params = {}
        if self.user:
            user_info = models.User.get_by_id(long(self.user_id))
            self.form.username.data = user_info.username
            self.form.name.data = user_info.name
            self.form.last_name.data = user_info.last_name
            self.form.country.data = user_info.country
            self.form.tz.data = user_info.tz
            providers_info = user_info.get_social_providers_info()
            if not user_info.password:
                params['local_account'] = False
            else:
                params['local_account'] = True
            params['used_providers'] = providers_info['used']
            params['unused_providers'] = providers_info['unused']
            params['country'] = user_info.country
            params['tz'] = user_info.tz

        return self.render_template('edit_profile.html', **params)

    def post(self):
        """ Get fields from POST dict """

        if not self.form.validate():
            return self.get()
        username = self.form.username.data.lower()
        name = self.form.name.data.strip()
        last_name = self.form.last_name.data.strip()
        country = self.form.country.data
        tz = self.form.tz.data

        try:
            user_info = models.User.get_by_id(long(self.user_id))

            try:
                message = ''
                # update username if it has changed and it isn't already taken
                if username != user_info.username:
                    user_info.unique_properties = ['username', 'email']
                    uniques = [
                        'User.username:%s' % username,
                        'User.auth_id:own:%s' % username,
                        ]
                    # Create the unique username and auth_id.
                    success, existing = Unique.create_multi(uniques)
                    if success:
                        # free old uniques
                        Unique.delete_multi(
                            ['User.username:%s' % user_info.username, 'User.auth_id:own:%s' % user_info.username])
                        # The unique values were created, so we can save the user.
                        user_info.username = username
                        user_info.auth_ids[0] = 'own:%s' % username
                        message += _('Your new username is <strong>{}</strong>').format(username)

                    else:
                        message += _(
                            'The username <strong>{}</strong> is already taken. Please choose another.').format(
                            username)
                        # At least one of the values is not unique.
                        self.add_message(message, 'error')
                        return self.get()
                user_info.name = name
                user_info.last_name = last_name
                user_info.country = country
                user_info.tz = tz
                user_info.put()
                message += " " + _('Thanks, your settings have been saved.')
                self.add_message(message, 'success')
                return self.get()

            except (AttributeError, KeyError, ValueError), e:
                logging.error('Error updating profile: ' + e)
                message = _('Unable to update profile. Please try again later.')
                self.add_message(message, 'error')
                return self.get()

        except (AttributeError, TypeError), e:
            login_error_message = _('Sorry you are not logged in.')
            self.add_message(login_error_message, 'error')
            self.redirect_to('login')

    @webapp2.cached_property
    def form(self):
        f = forms.EditProfileForm(self)
        f.country.choices = self.countries_tuple
        f.tz.choices = self.tz
        return f


class EditPasswordHandler(BaseHandler):
    """
    Handler for Edit User Password
    """

    @user_required
    def get(self):
        """ Returns a simple HTML form for editing password """

        params = {}
        return self.render_template('edit_password.html', **params)

    def post(self):
        """ Get fields from POST dict """

        if not self.form.validate():
            return self.get()
        current_password = self.form.current_password.data.strip()
        password = self.form.password.data.strip()

        try:
            user_info = models.User.get_by_id(long(self.user_id))
            auth_id = "own:%s" % user_info.username

            # Password to SHA512
            current_password = utils.hashing(current_password, self.app.config.get('salt'))
            try:
                user = models.User.get_by_auth_password(auth_id, current_password)
                # Password to SHA512
                password = utils.hashing(password, self.app.config.get('salt'))
                user.password = security.generate_password_hash(password, length=12)
                user.put()

                # send email
                subject = self.app.config.get('app_name') + " Account Password Changed"

                # load email's template
                template_val = {
                    "app_name": self.app.config.get('app_name'),
                    "first_name": user.name,
                    "username": user.username,
                    "email": user.email,
                    "reset_password_url": self.uri_for("password-reset", _full=True)
                }
                email_body_path = "emails/password_changed.txt"
                email_body = self.jinja2.render_template(email_body_path, **template_val)
                email_url = self.uri_for('taskqueue-send-email')
                taskqueue.add(url=email_url, params={
                    'to': user.email,
                    'subject': subject,
                    'body': email_body,
                    'sender': self.app.config.get('contact_sender'),
                    })

                #Login User
                self.auth.get_user_by_password(user.auth_ids[0], password)
                self.add_message(_('Password changed successfully.'), 'success')
                return self.redirect_to('edit-profile')
            except (InvalidAuthIdError, InvalidPasswordError), e:
                # Returns error message to self.response.write in
                # the BaseHandler.dispatcher
                message = _("Incorrect password! Please enter your current password to change your account settings.")
                self.add_message(message, 'error')
                return self.redirect_to('edit-password')
        except (AttributeError, TypeError), e:
            login_error_message = _('Sorry you are not logged in.')
            self.add_message(login_error_message, 'error')
            self.redirect_to('login')

    @webapp2.cached_property
    def form(self):
        return forms.EditPasswordForm(self)


class EditEmailHandler(BaseHandler):
    """
    Handler for Edit User's Email
    """

    @user_required
    def get(self):
        """ Returns a simple HTML form for edit email """

        params = {}
        if self.user:
            user_info = models.User.get_by_id(long(self.user_id))
            params['current_email'] = user_info.email

        return self.render_template('edit_email.html', **params)

    def post(self):
        """ Get fields from POST dict """

        if not self.form.validate():
            return self.get()
        new_email = self.form.new_email.data.strip()
        password = self.form.password.data.strip()

        try:
            user_info = models.User.get_by_id(long(self.user_id))
            auth_id = "own:%s" % user_info.username
            # Password to SHA512
            password = utils.hashing(password, self.app.config.get('salt'))

            try:
                # authenticate user by its password
                user = models.User.get_by_auth_password(auth_id, password)

                # if the user change his/her email address
                if new_email != user.email:

                    # check whether the new email has been used by another user
                    aUser = models.User.get_by_email(new_email)
                    if aUser is not None:
                        message = _("The email %s is already registered." % new_email)
                        self.add_message(message, 'error')
                        return self.redirect_to("edit-email")

                    # send email
                    subject = _("%s Email Changed Notification" % self.app.config.get('app_name'))
                    user_token = models.User.create_auth_token(self.user_id)
                    confirmation_url = self.uri_for("email-changed-check",
                                                    user_id=user_info.get_id(),
                                                    encoded_email=utils.encode(new_email),
                                                    token=user_token,
                                                    _full=True)

                    # load email's template
                    template_val = {
                        "app_name": self.app.config.get('app_name'),
                        "first_name": user.name,
                        "username": user.username,
                        "new_email": new_email,
                        "confirmation_url": confirmation_url,
                        "support_url": self.uri_for("contact", _full=True)
                    }

                    old_body_path = "emails/email_changed_notification_old.txt"
                    old_body = self.jinja2.render_template(old_body_path, **template_val)

                    new_body_path = "emails/email_changed_notification_new.txt"
                    new_body = self.jinja2.render_template(new_body_path, **template_val)

                    email_url = self.uri_for('taskqueue-send-email')
                    taskqueue.add(url=email_url, params={
                        'to': user.email,
                        'subject': subject,
                        'body': old_body,
                        })
                    taskqueue.add(url=email_url, params={
                        'to': new_email,
                        'subject': subject,
                        'body': new_body,
                        })

                    # display successful message
                    msg = _(
                        "Please check your new email for confirmation. Your email will be updated after confirmation.")
                    self.add_message(msg, 'success')
                    return self.redirect_to('edit-profile')

                else:
                    self.add_message(_("You didn't change your email."), "warning")
                    return self.redirect_to("edit-email")


            except (InvalidAuthIdError, InvalidPasswordError), e:
                # Returns error message to self.response.write in
                # the BaseHandler.dispatcher
                message = _("Incorrect password! Please enter your current password to change your account settings.")
                self.add_message(message, 'error')
                return self.redirect_to('edit-email')

        except (AttributeError, TypeError), e:
            login_error_message = _('Sorry you are not logged in.')
            self.add_message(login_error_message, 'error')
            self.redirect_to('login')

    @webapp2.cached_property
    def form(self):
        return forms.EditEmailForm(self)


class PasswordResetHandler(BaseHandler):
    """
    Password Reset Handler with Captcha
    """

    def get(self):
        chtml = captcha.displayhtml(
            public_key=self.app.config.get('captcha_public_key'),
            use_ssl=(self.request.scheme == 'https'),
            error=None)
        if self.app.config.get('captcha_public_key') == "PUT_YOUR_RECAPCHA_PUBLIC_KEY_HERE" or \
                        self.app.config.get('captcha_private_key') == "PUT_YOUR_RECAPCHA_PUBLIC_KEY_HERE":
            chtml = '<div class="alert alert-error"><strong>Error</strong>: You have to ' \
                    '<a href="http://www.google.com/recaptcha/whyrecaptcha" target="_blank">sign up ' \
                    'for API keys</a> in order to use reCAPTCHA.</div>' \
                    '<input type="hidden" name="recaptcha_challenge_field" value="manual_challenge" />' \
                    '<input type="hidden" name="recaptcha_response_field" value="manual_challenge" />'
        params = {
            'captchahtml': chtml,
            }
        return self.render_template('password_reset.html', **params)

    def post(self):
        # check captcha
        challenge = self.request.POST.get('recaptcha_challenge_field')
        response = self.request.POST.get('recaptcha_response_field')
        remoteip = self.request.remote_addr

        cResponse = captcha.submit(
            challenge,
            response,
            self.app.config.get('captcha_private_key'),
            remoteip)

        if cResponse.is_valid:
            # captcha was valid... carry on..nothing to see here
            pass
        else:
            _message = _('Wrong image verification code. Please try again.')
            self.add_message(_message, 'error')
            return self.redirect_to('password-reset')
            #check if we got an email or username
        email_or_username = str(self.request.POST.get('email_or_username')).lower().strip()
        if utils.is_email_valid(email_or_username):
            user = models.User.get_by_email(email_or_username)
            _message = _("If the email address you entered") + " (<strong>%s</strong>) " % email_or_username
        else:
            auth_id = "own:%s" % email_or_username
            user = models.User.get_by_auth_id(auth_id)
            _message = _("If the username you entered") + " (<strong>%s</strong>) " % email_or_username

        _message = _message + _("is associated with an account in our records, you will receive "
                                "an email from us with instructions for resetting your password. "
                                "<br>If you don't receive instructions within a minute or two, "
                                "check your email's spam and junk filters, or ") + \
                   '<a href="' + self.uri_for('contact') + '">' + _('contact us') + '</a> ' + _(
            "for further assistance.")

        if user is not None:
            user_id = user.get_id()
            token = models.User.create_auth_token(user_id)
            email_url = self.uri_for('taskqueue-send-email')
            reset_url = self.uri_for('password-reset-check', user_id=user_id, token=token, _full=True)
            subject = _("%s Password Assistance" % self.app.config.get('app_name'))

            # load email's template
            template_val = {
                "username": user.username,
                "email": user.email,
                "reset_password_url": reset_url,
                "support_url": self.uri_for("contact", _full=True),
                "app_name": self.app.config.get('app_name'),
                }

            body_path = "emails/reset_password.txt"
            body = self.jinja2.render_template(body_path, **template_val)
            taskqueue.add(url=email_url, params={
                'to': user.email,
                'subject': subject,
                'body': body,
                'sender': self.app.config.get('contact_sender'),
                })
        self.add_message(_message, 'warning')
        return self.redirect_to('login')


class PasswordResetCompleteHandler(BaseHandler):
    """
    Handler to process the link of reset password that received the user
    """

    def get(self, user_id, token):
        verify = models.User.get_by_auth_token(int(user_id), token)
        params = {}
        if verify[0] is None:
            message = _('The URL you tried to use is either incorrect or no longer valid. '
                        'Enter your details again below to get a new one.')
            self.add_message(message, 'warning')
            return self.redirect_to('password-reset')

        else:
            return self.render_template('password_reset_complete.html', **params)

    def post(self, user_id, token):
        verify = models.User.get_by_auth_token(int(user_id), token)
        user = verify[0]
        password = self.form.password.data.strip()
        if user and self.form.validate():
            # Password to SHA512
            password = utils.hashing(password, self.app.config.get('salt'))

            user.password = security.generate_password_hash(password, length=12)
            user.put()
            # Delete token
            models.User.delete_auth_token(int(user_id), token)
            # Login User
            self.auth.get_user_by_password(user.auth_ids[0], password)
            self.add_message(_('Password changed successfully.'), 'success')
            return self.redirect_to('home')

        else:
            self.add_message(_('The two passwords must match.'), 'error')
            return self.redirect_to('password-reset-check', user_id=user_id, token=token)

    @webapp2.cached_property
    def form(self):
        return forms.PasswordResetCompleteForm(self)


class EmailChangedCompleteHandler(BaseHandler):
    """
    Handler for completed email change
    Will be called when the user click confirmation link from email
    """

    def get(self, user_id, encoded_email, token):
        verify = models.User.get_by_auth_token(int(user_id), token)
        email = utils.decode(encoded_email)
        if verify[0] is None:
            message = _('The URL you tried to use is either incorrect or no longer valid.')
            self.add_message(message, 'warning')
            self.redirect_to('home')

        else:
            # save new email
            user = verify[0]
            user.email = email
            user.put()
            # delete token
            models.User.delete_auth_token(int(user_id), token)
            # add successful message and redirect
            message = _('Your email has been successfully updated.')
            self.add_message(message, 'success')
            self.redirect_to('edit-profile')



class MediaUploadHandler(BaseHandler):
    """
    Handler for returning image upload information
    """

    def post(self):
        self.fileupload = self.request.POST.get("file", None)
        self.blob = self.fileupload.value
        self.filename = self.fileupload.filename
        self.orig_filename = self.filename
        self.mime_type = self.fileupload.type

        self.image_widths = ['100','320','640','1200']
        #The list that is returned
        self.image_list = []
        if self.mime_type == "image/jpeg" or self.mime_type == "image/png":
            for self.image_width in self.image_widths:
                #Each indivdual JSON object
                self.image_width_dict = {}
                #Set the width of the file
                self.image_width_dict['width'] = self.image_width
                #Capture the bytes
                self.image = images.Image(self.blob)
                #Resize the image per the file list above
                self.image.resize(int(self.image_width))
                #Set the height
                self.image_width_dict['height'] = str(self.image.height)
                #Auto modify the image contrast levels
                self.image.im_feeling_lucky()
                #Convert the type of image
                self.image_new_size = self.image.execute_transforms(output_encoding=images.PNG)
                #Set the response dictionary type to PNG
                self.image_width_dict['filetype'] = "image/png"
                self.image_width_dict['file_cat'] = "image"
                #Set bucket filename for cloud storage
                self.filename = '/bealittlecloser/' + self.orig_filename + '_' + self.image_width
                #Open and save bytes
                with gcs.open(self.filename, 'w', content_type='image/png') as f:
                    f.write(self.image_new_size)
                    #set blobstore filename
                self.blobstore_filename = '/gs' + self.filename
                #Create and get the key
                self.image_width_dict['blobstore_key'] = blobstore.create_gs_key(self.blobstore_filename)

                #Add record to list
                self.image_list.append(self.image_width_dict)

        elif self.mime_type == "video/mp4":
            self.video_dict = {}
            self.video_dict['filetype'] = self.mime_type
            self.video_dict['file_cat'] = "video"

            self.filename = '/bealittlecloser/' + self.orig_filename
            #Open and save bytes
            with gcs.open(self.filename, 'w', content_type=self.mime_type) as f:
                f.write(self.blob)
                #set blobstore filename
            self.blobstore_filename = '/gs' + self.filename
            #Create and get the key
            self.video_dict['blobstore_key'] = blobstore.create_gs_key(self.blobstore_filename)
            #Add record to list
            self.image_list.append(self.video_dict)


        elif self.mime_type == "audio/mp3" or self.mime_type =="audio/mpeg" or self.mime_type=="audio/x-m4a":
            self.audio_dict = {}
            self.audio_dict['filetype'] = self.mime_type
            self.audio_dict['file_cat'] = "audio"

            self.filename = '/bealittlecloser/' + self.orig_filename
            #Open and save bytes
            with gcs.open(self.filename, 'w', content_type=self.mime_type) as f:
                f.write(self.blob)
                #set blobstore filename
            self.blobstore_filename = '/gs' + self.orig_filename
            #Create and get the key
            self.audio_dict['blobstore_key'] = blobstore.create_gs_key(self.blobstore_filename)
            #Add record to list
            self.image_list.append(self.audio_dict)

        else:
            self.other_dict = {}
            self.other_dict['filetype'] = self.mime_type
            self.other_dict['file_cat'] = "unknown"

            self.filename = '/bealittlecloser/' + self.orig_filename
            #Open and save bytes
            with gcs.open(self.filename, 'w', content_type=self.mime_type) as f:
                f.write(self.blob)
                #set blobstore filename
            self.blobstore_filename = '/gs' + self.filename
            #Create and get the key
            self.other_dict['blobstore_key'] = blobstore.create_gs_key(self.blobstore_filename)
            #Add record to list
            self.image_list.append(self.other_dict)

        self.return_json ={}
        self.return_json['results'] = self.image_list
        self.return_json['filename'] = self.orig_filename
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps(self.return_json))



class GetMediaHandler(blobstore_handlers.BlobstoreDownloadHandler, BaseHandler):
    """
    Handler to retrieve the media for the blurb
    """
    def get(self, media_key):
        if not blobstore.get(media_key):
            self.error(404)
        else:
            self.send_blob(media_key)



class MapHandler(BaseHandler):
    """
    Handler for requesting map information
    """

    def get(self):
        """ Returns a simple HTML form for home """
        params = {}
        return self.render_template('map.html', **params)

class SingleConnectionHandler(BaseHandler):
    def get(self, connection_id):
        """ Returns a simple HTML form for home """
        params = {'connection_id':connection_id}
        return self.render_template('connection.html', **params)

class ConnectionHandler(BaseHandler):
    """
    Handler for requesting successful connection information
    """

    def get(self):
        """ Returns a simple HTML form for home """
        params = {}
        return self.render_template('connections.html', **params)

class BlogHandler(BaseHandler):
    """
    Handler for requesting successful connection information
    """

    def get(self):
        """ Returns a simple HTML form for home """
        params = {}
        return self.render_template('blog.html', **params)

class MobileHandler(BaseHandler):
    """
    Handler for requesting successful connection information
    """

    def get(self):
        """ Returns a simple HTML form for home """
        params = {}
        return self.render_template('mobile.html', **params)

class EulaHandler(BaseHandler):
    """
    Handler for requesting successful connection information
    """

    def get(self):
        """ Returns a simple HTML form for home """
        params = {}
        return self.render_template('eula.html', **params)

class FAQHandler(BaseHandler):
    """
    Handler for requesting successful connection information
    """

    def get(self):
        """ Returns a simple HTML form for home """
        params = {}
        return self.render_template('faq.html', **params)


class PaymentHandler(BaseHandler):
    """
    Handler for requesting successful connection information
    """

    def get(self):
        """ Returns a simple HTML form for home """
        params = {}
        return self.render_template('payment.html', **params)

class ProfileHandler(BaseHandler):
    """
    Handler for requesting successful connection information
    """

    def get(self):
        """ Returns a simple HTML form for home """
        params = {}
        return self.render_template('profile.html', **params)

class PinterestHandler(BaseHandler):
    """
    Handler for requesting successful connection information
    """

    def get(self):
        """ Returns a simple HTML form for home """
        params = {}
        return self.render_template('pinterest-0fdc7.html', **params)



class ConnectionApiHandler(BaseHandler):
    """
    Handler to process API requests for connections
    """

    def get(self):
        self.response.headers['Content-Type'] = 'application/json'
        obj = {
            'success': 'some var',
            'payload': 'some var',
            }
        self.response.out.write(json.dumps(obj))

    def post(self):

        uastring = self.request.user_agent,
        ip = self.request.remote_addr,
        timestamp = utils.get_date_time()

        ip = ip[0]
        uastring = uastring[0]

        type = self.request.get('type')
        title = self.request.get('title')
        summary = self.request.get('summary')
        connection_name = self.request.get('connection_name')
        request_reason = self.request.get('request_reason')
        private_location = self.request.get('private_location')
        personalized_message = self.request.get('personalized_message')


        # Create New Connection DB Instance

        new_connection = Connection()

        new_connection.type = type
        new_connection.title = title
        new_connection.summary = summary
        new_connection.connection_name = connection_name
        new_connection.request_reason = request_reason
        new_connection.private_loc = private_location
        new_connection.personalized_message = personalized_message
        new_connection.request_uastring = uastring
        new_connection.request_ip = ip

        new_connection_key = new_connection.put()

class BlogRetrieverHandler(BaseHandler):
    def get(self):
        post_type = self.request.get("post_type")
        tag = self.request.get("tag")
        limit = self.request.get("limit")
        offset = self.request.get("offset")

        if tag !="":
            tag = "&tag=" + tag
        else:
            tag="#alittlecloser"
        if limit !="":
            limit = "&limit=" + limit
        if offset !="":
            offset = "&offset=" + offset

        # USE THESE FOR PRODUCTION
        api_key = 'tfoQU3EjFMNXdSRWDqCqfWU6AxoBtDMa59DfmsfhfImeeFN6kO'
        domain = 'bealittlecloser-com.tumblr.com'

        info_url = "http://api.tumblr.com/v2/blog/%s/info?api_key=%s" % (domain, api_key)
        likes_url = "http://api.tumblr.com/v2/blog/%s/likes?api_key=%s" % (domain, api_key)
        posts_url = "http://api.tumblr.com/v2/blog/%s/posts/%s?api_key=%s%s%s%s" % (domain, post_type, api_key, tag, limit, offset)

        result = urlfetch.fetch(posts_url)
        if result.status_code == 200:

            out_json = json.loads(result.content)
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(json.dumps(out_json['response']['posts']))

class MailchimpUserHandler(BaseHandler):
    def post(self):
        groupings = []
        email = self.request.get('email')
        opt_in_ip = self.request.get('ip')
        first_name = self.request.get('fname')
        last_name = self.request.get('lname')
        opt_in_time = self.request.get('time')
        mc_function = self.request.get('function')
        mc_url = self.app.config.get('mailchimp_post_url')
        mc_list_id = self.app.config.get('mailchimp_list')
        mc_apikey = self.app.config.get('mailchimp_api_key')
        if mc_function == "trial_add":
            groupings.append(self.app.config.get('mailchimp_segment_trial'))

            form_fields = {}
            merge_vars = {}

            email_dict = {}
            email_dict['email'] = email

            groupings = []
            group_id = {}
            group_id['name'] = self.app.config.get('mailchimp_group_name')
            group_id['groups'] = ['ALC User']
            groupings.append(group_id)
            merge_vars['groupings'] = groupings

            if first_name:
                merge_vars['FNAME'] = first_name
            if last_name:
                merge_vars['LNAME'] = first_name

            form_fields['apikey'] = mc_apikey
            form_fields['id'] = mc_list_id
            form_fields['double_optin'] = False
            form_fields['email']= email_dict
            form_fields['merge_vars'] = merge_vars

            form_data = json.dumps(form_fields)

            result = urlfetch.fetch(url=mc_url+"/lists/subscribe",
                                    payload=form_data,
                                    method=urlfetch.POST,
                                    headers={})

            self.return_json ={}
            self.return_json['message'] = "Success"
            self.response.headers['Content-Type'] = 'application/json'
            self.response.out.write(json.dumps(self.return_json))

class HomeRequestHandler(RegisterBaseHandler):
    """
    Handler to show the home page
    """

    def get(self):
        """ Returns a simple HTML form for home """
        params = {}
        return self.render_template('home.html', **params)

