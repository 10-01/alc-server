from webapp2_extras.appengine.auth.models import User
from google.appengine.ext import ndb
import json

from alittlecloser_api_messages import ConnectionResponseMessage, SingleConnectionReponseMessage, CommentsResponseMessage, MediaJsonFinalResponse, LatLngMessage


class User(User):
    """
    Universal user model. Can be used with App Engine's default users API,
    own auth or third party authentication methods (OpenID, OAuth etc).
    based on https://gist.github.com/kylefinley
    """

    #: Creation date.
    created = ndb.DateTimeProperty(auto_now_add=True)
    #: Modification date.
    updated = ndb.DateTimeProperty(auto_now=True)
    #: User defined unique name, also used as key_name.
    # Not used by OpenID
    username = ndb.StringProperty()
    #: User Name
    name = ndb.StringProperty()
    #: User Last Name
    last_name = ndb.StringProperty()
    #: User email
    email = ndb.StringProperty()
    #: Hashed password. Only set for own authentication.
    # Not required because third party authentication
    # doesn't use password.
    password = ndb.StringProperty()
    #: User Country
    country = ndb.StringProperty()
    #: User TimeZone
    tz = ndb.StringProperty()
    #: Account activation verifies email
    activated = ndb.BooleanProperty(default=False)

    type= ndb.StringProperty()
    loc_name= ndb.StringProperty()
    imgs= ndb.StringProperty()
    requests= ndb.StringProperty()
    summary= ndb.StringProperty()


    @classmethod
    def get_by_email(cls, email):
        """Returns a user object based on an email.

        :param email:
            String representing the user email. Examples:

        :returns:
            A user object.
        """
        return cls.query(cls.email == email).get()

    @classmethod
    def create_resend_token(cls, user_id):
        entity = cls.token_model.create(user_id, 'resend-activation-mail')
        return entity.token

    @classmethod
    def validate_resend_token(cls, user_id, token):
        return cls.validate_token(user_id, 'resend-activation-mail', token)

    @classmethod
    def delete_resend_token(cls, user_id, token):
        cls.token_model.get_key(user_id, 'resend-activation-mail', token).delete()

    def get_social_providers_names(self):
        social_user_objects = SocialUser.get_by_user(self.key)
        result = []
#        import logging
        for social_user_object in social_user_objects:
#            logging.error(social_user_object.extra_data['screen_name'])
            result.append(social_user_object.provider)
        return result

    def get_social_providers_info(self):
        providers = self.get_social_providers_names()
        result = {'used': [], 'unused': []}
        for k,v in SocialUser.PROVIDERS_INFO.items():
            if k in providers:
                result['used'].append(v)
            else:
                result['unused'].append(v)
        return result

    @classmethod
    def get_user_by_id(cls, user_id):
        return cls.get_by_id(int(user_id))


class LogVisit(ndb.Model):
    user = ndb.KeyProperty(kind=User)
    uastring = ndb.StringProperty()
    ip = ndb.StringProperty()
    timestamp = ndb.StringProperty()


class LogEmail(ndb.Model):
    sender = ndb.StringProperty(
        required=True)
    to = ndb.StringProperty(
        required=True)
    subject = ndb.StringProperty(
        required=True)
    body = ndb.TextProperty()
    when = ndb.DateTimeProperty()


class SocialUser(ndb.Model):
    PROVIDERS_INFO = { # uri is for OpenID only (not OAuth)
        'google': {'name': 'google', 'label': 'Google', 'uri': 'gmail.com'},
        'github': {'name': 'github', 'label': 'Github', 'uri': ''},
        'facebook': {'name': 'facebook', 'label': 'Facebook', 'uri': ''},
        'linkedin': {'name': 'linkedin', 'label': 'LinkedIn', 'uri': ''},
        'myopenid': {'name': 'myopenid', 'label': 'MyOpenid', 'uri': 'myopenid.com'},
        'twitter': {'name': 'twitter', 'label': 'Twitter', 'uri': ''},
        'yahoo': {'name': 'yahoo', 'label': 'Yahoo!', 'uri': 'yahoo.com'},
    }

    user = ndb.KeyProperty(kind=User)
    provider = ndb.StringProperty()
    uid = ndb.StringProperty()
    extra_data = ndb.JsonProperty()

    @classmethod
    def get_by_user(cls, user):
        return cls.query(cls.user == user).fetch()

    @classmethod
    def get_by_user_and_provider(cls, user, provider):
        return cls.query(cls.user == user, cls.provider == provider).get()

    @classmethod
    def get_by_provider_and_uid(cls, provider, uid):
        return cls.query(cls.provider == provider, cls.uid == uid).get()

    @classmethod
    def check_unique_uid(cls, provider, uid):
        # pair (provider, uid) should be unique
        test_unique_provider = cls.get_by_provider_and_uid(provider, uid)
        if test_unique_provider is not None:
            return False
        else:
            return True
    
    @classmethod
    def check_unique_user(cls, provider, user):
        # pair (user, provider) should be unique
        test_unique_user = cls.get_by_user_and_provider(user, provider)
        if test_unique_user is not None:
            return False
        else:
            return True

    @classmethod
    def check_unique(cls, user, provider, uid):
        # pair (provider, uid) should be unique and pair (user, provider) should be unique
        return cls.check_unique_uid(provider, uid) and cls.check_unique_user(provider, user)
    
    @staticmethod
    def open_id_providers():
        return [k for k,v in SocialUser.PROVIDERS_INFO.items() if v['uri']]


class Connection(ndb.Model):
    """
    Model for the creation of connection results
    """

    #: Creation date.
    created = ndb.DateTimeProperty(auto_now_add=True)
    #: Modification date.
    updated = ndb.DateTimeProperty(auto_now=True)
    # Link to blog posts about, with some metadata about the post
    blog_url = ndb.JsonProperty()
    # T/f for if connection is completed
    completed = ndb.BooleanProperty(default=False)
    # Date completed
    completion_date = ndb.DateTimeProperty()
    #Connection stage (0=submitted, 1= accepted, 2=completed)
    connection_stage =  ndb.IntegerProperty(default=0)
    #Lets us know which table to lookup the user or person in
    connection_type = ndb.StringProperty()
    #json_obj of related media
    media =  ndb.JsonProperty()
    #latitude of connection person/thing
    latitude =  ndb.FloatProperty()
    #longitude of connection person/thing
    longitude = ndb.FloatProperty()
    #Location geopoint
    loc_geopt = ndb.GeoPtProperty()
    #name of the locations
    loc_name =  ndb.StringProperty()
    #exact address for viewing only by the admins
    private_loc =  ndb.StringProperty()
    #map marker color
    marker_color =  ndb.StringProperty()
    #map marker size
    marker_size =  ndb.StringProperty(default="medium")
    #map marker symbol
    marker_symbol = ndb.StringProperty()
    #Key of user requesting
    user_key =  ndb.KeyProperty()
    #name of user requesting
    user_name =  ndb.StringProperty()
    #picture of user requesting
    user_picture =  ndb.StringProperty()
    #personalized message on request
    personalized_message = ndb.StringProperty()
    #primary media item
    primary_media =  ndb.StringProperty()
    #IP from requesting user
    ip = ndb.StringProperty()
    #UA string of user requesting
    uastring = ndb.TextProperty()
    #posts related to this one (populated by analytics)
    related_post_id =  ndb.StringProperty()
    #Why the request is being made (private for admins
    request_reason = ndb.StringProperty()
    #public summary of the request
    summary =  ndb.StringProperty()
    #admin added body
    body =  ndb.StringProperty()
    #title of the request
    title =  ndb.StringProperty()
    #social media share links
    social_media_json =  ndb.StringProperty()
    #request type - give or get?
    type =  ndb.StringProperty()
    #connection key to the user receiving the request
    personthing_key = ndb.KeyProperty()
    #name of person receiving item
    personthing_name = ndb.StringProperty()


    def to_message(self, media_response):
        """Turns the Connection entity into a ProtoRPC object.
        """
        if self.personthing_key:
            self.personthing_id = str(self.personthing_key.id())
        else:
            self.personthing_id = ""

        if self.user_key:
            self.user_id = self.user_key.id()
        else:
            self.user_id = None



        return ConnectionResponseMessage(title = self.title,
                                         type = self.type,
                                         blog_url=self.blog_url,
                                         completed = self.completed,
                                         completion_date = self.completion_date,
                                         connection_stage = self.connection_stage,
                                         connection_type = self.connection_type,
                                         latitude = self.latitude,
                                         longitude = self.longitude,
                                         loc_name = self.loc_name,
                                         marker_color = self.marker_color,
                                         marker_size = self.marker_size,
                                         marker_symbol = self.marker_symbol,
                                         media = media_response,
                                         user_id =  self.user_id,
                                         user_name =  self.user_name,
                                         user_picture = self.user_picture,
                                         personthing_id = self.personthing_id,
                                         personthing_name = self.personthing_name,
                                         primary_media = self.primary_media,
                                         summary = self.summary,
                                         req_reason = self.request_reason,
                                         social_media_json = self.social_media_json,
                                         created = self.created,
                                         updated = self.updated,
                                         id = self.key.id())

    def to_indiv_message(self,media_response):
        """Turns the Connection entity into a ProtoRPC object.
        """
        if self.personthing_key:
            self.personthing_id = str(self.personthing_key.id())
        else:
            self.personthing_id = ""

        if self.user_key:
            self.user_id = self.user_key.id()
        else:
            self.user_id = None

        return SingleConnectionReponseMessage(title = self.title,
                                         type = self.type,
                                         blog_url=self.blog_url,
                                         completed = self.completed,
                                         completion_date = self.completion_date,
                                         connection_stage = self.connection_stage,
                                         connection_type = self.connection_type,
                                         latitude = self.latitude,
                                         longitude = self.longitude,
                                         loc_name = self.loc_name,
                                         marker_color = self.marker_color,
                                         marker_size = self.marker_size,
                                         marker_symbol = self.marker_symbol,
                                         media = media_response,
                                         user_id =  self.user_id,
                                         user_name =  self.user_name,
                                         user_picture = self.user_picture,
                                         personthing_id = self.personthing_id,
                                         personthing_name = self.personthing_name,
                                         primary_media = self.primary_media,
                                         summary = self.summary,
                                         req_reason = self.request_reason,
                                         body = self.body,
                                         social_media_json = self.social_media_json,
                                         created = self.created,
                                         updated = self.updated,
                                         id = self.key.id())


    @classmethod
    def get_connections(cls, curs, limit, filter_dictionary):
        qry_var = cls.query()
        for k,v in filter_dictionary.iteritems():
            qry_var_new = qry_var.filter(cls._properties[k] == v)
            qry_var = qry_var_new

        return qry_var.order(-cls.created).fetch_page(limit, start_cursor=curs)


    @classmethod
    def get_connection_by_id(cls, connection_id):
        return cls.get_by_id(int(connection_id))

    @classmethod
    def get_connection_by_title(cls, title_name):
        return cls.query(cls.title == title_name).fetch()

    @classmethod
    def get_connections_by_user_id_status(cls, user_key):
        return cls.query(ndb.AND(cls.user_key == user_key, cls.connection_stage == 0)).fetch()



class PeopleThing(ndb.Model):
    """
      Model for the person or thing that is getting the gift
    """

    #: Creation date.
    created = ndb.DateTimeProperty(auto_now_add=True)
    #: Modification date.
    updated = ndb.DateTimeProperty(auto_now=True)
    #json_obj of related media
    media =  ndb.JsonProperty(default="{'media': 'none'}")
    #latitude of connection person/thing
    latitude =  ndb.FloatProperty(default=0)
    #longitude of connection person/thing
    longitude = ndb.FloatProperty(default=0)
    #name of location of the person/thing
    loc_name = ndb.StringProperty()
    #Key to user that created
    user_key = ndb.KeyProperty()
    #name of user that created
    user_name = ndb.StringProperty()
    #Name of the person/thing
    name = ndb.StringProperty()
    #age
    age = ndb.IntegerProperty()
    #type of thing/person
    type = ndb.StringProperty()

    @classmethod
    def get_person_by_id(cls, personthing_id):
        return cls.get_by_id(int(personthing_id))

class Relationships(ndb.Model):
    """
      Model for the relationship between people, users, and things
    """

    #: Creation date.
    created = ndb.DateTimeProperty(auto_now_add=True)
    #: Modification date.
    updated = ndb.DateTimeProperty(auto_now=True)
    #Key to user that created
    user_key = ndb.KeyProperty()
    #name of user that created
    user_name = ndb.StringProperty()
    #user or peoplething
    type = ndb.StringProperty()
    #key to the people table
    people_key = ndb.KeyProperty()
    #name of the personthing
    people_name = ndb.StringProperty()
    #type of relationship (mom, home, brother)
    relationship_type = ndb.StringProperty()
    #relationship start date
    relationship_start_date = ndb.DateTimeProperty()
    #relationship end date
    relationship_end_date = ndb.DateTimeProperty()

    @classmethod
    def get_relationship_by_id(cls, relationship_id):
        return cls.get_by_id(int(relationship_id))

class Comments(ndb.Model):
    """
      Model for the comments about the connections
    """

    #: Creation date.
    created = ndb.DateTimeProperty(auto_now_add=True)
    #: Modification date.
    updated = ndb.DateTimeProperty(auto_now=True)
    #json_obj of related media
    media =  ndb.JsonProperty()
    #Key to user that created
    user_key = ndb.KeyProperty()
    #name of user that created
    user_name = ndb.StringProperty()
    #type of post -- photo, video, html
    post_type = ndb.StringProperty()
    #post tags
    tags = ndb.StringProperty()
    #title of post
    title = ndb.StringProperty()
    #body of the blog post
    body = ndb.StringProperty()
    #person key post is associated with
    personthing_key = ndb.KeyProperty()
    #name of personthing
    personthing_name = ndb.StringProperty()
    #key to connection
    connection_key = ndb.KeyProperty()
    #title of connection
    connection_title = ndb.StringProperty()
    #social media sharing
    social_media_json = ndb.JsonProperty()
    #IP from requesting user
    ip = ndb.StringProperty()
    #UA string of user requesting
    uastring = ndb.TextProperty()

    def to_comment_message(self):
        """Turns the Connection entity into a ProtoRPC object.
        """
        if self.personthing_key:
            self.personthing_id = str(self.personthing_key.id())
        else:
            self.personthing_id = ""

        if self.user_key:
            self.user_id = str(self.user_key.id())
        else:
            self.user_id = ""
        if self.connection_key:
            self.connection_id = str(self.connection_key.id())
        else:
            self.connection_id = ""


        return CommentsResponseMessage(title = self.title,
                                     post_type = self.post_type,
                                     body = self.body,
                                     media = self.media,
                                     tags = self.tags,
                                     personthing_id = self.personthing_id,
                                     personthing_name = self.personthing_name,
                                     user_id = self.user_id,
                                     user_name = self.user_name,
                                     connection_id = self.connection_id,
                                     connection_title = self.connection_title,
                                     social_media_json = self.social_media_json,
                                     created = self.created,
                                     updated = self.updated,
                                     comment_id = self.key.id())

    @classmethod
    def get_comment_by_id(cls, comment_id):
        return cls.get_by_id(int(comment_id))

    @classmethod
    def get_comments(cls, curs, limit, filter_dictionary):
        qry_var = cls.query()
        for k,v in filter_dictionary.iteritems():
            qry_var_new = qry_var.filter(cls._properties[k] == v)
            qry_var = qry_var_new

        return qry_var.order(-cls.created).fetch_page(limit, start_cursor=curs)

class ApiKeys(ndb.Model):
    #: Creation date.
    created = ndb.DateTimeProperty(auto_now_add=True)
    #: Modification date.
    updated = ndb.DateTimeProperty(auto_now=True)
    #user id the key is associated with
    user_id = ndb.IntegerProperty()
    #user_name
    user_name = ndb.StringProperty()
    #total calls
    total_calls = ndb.IntegerProperty(default=0)
    #role of the user
    role = ndb.StringProperty()

    @classmethod
    def get_apikey_by_id(cls, apikey_id):
        return cls.get_by_id(int(apikey_id))

    @classmethod
    def get_apikey_by_user_id(cls, user_id):
        if user_id:
            return cls.query(cls.user_id==int(user_id)).fetch()[0]

class Locations(ndb.Model):
    #: Creation date.
    created = ndb.DateTimeProperty(auto_now_add=True)
    #: Modification date.
    updated = ndb.DateTimeProperty(auto_now=True)
    # Link to blog posts about, with some metadata about the post
    blog_url = ndb.JsonProperty()
    #latitude of connection person/thing
    latitude =  ndb.FloatProperty()
    #longitude of connection person/thing
    longitude = ndb.FloatProperty()
    #Location geopoint
    loc_geopt = ndb.GeoPtProperty()
    #name of the locations
    loc_name =  ndb.StringProperty()
    #IP from requesting user
    ip = ndb.StringProperty()
    #UA string of user requesting
    uastring = ndb.TextProperty()
    #title of the request
    title =  ndb.StringProperty()
    #title of the request
    type =  ndb.StringProperty()

    @classmethod
    def get_locations(cls, curs, limit, filter_dictionary):
        qry_var = cls.query()
        for k,v in filter_dictionary.iteritems():
            qry_var_new = qry_var.filter(cls._properties[k] == v)
            qry_var = qry_var_new

        return qry_var.order(-cls.created).fetch_page(limit, start_cursor=curs)

    def to_location_message(self):
        """Turns the Connection entity into a ProtoRPC object.
        """

        return LatLngMessage(title = self.title,
                           created = self.created,
                           updated = self.updated,
                           blog_url = self.blog_url,
                           latitude = self.latitude,
                           longitude = self.longitude,
                           loc_name = self.loc_name,
                           type = self.type)

