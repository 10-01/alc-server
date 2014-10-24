#Created using IntelliJ IDEA.

from lib import utils

from google.appengine.ext import endpoints
import logging
import json
from json.decoder import WHITESPACE
import config
import os
from google.appengine.api import memcache



from google.appengine.datastore.datastore_query import Cursor
from google.appengine.ext import blobstore
from google.appengine.api import search
from google.appengine.ext import ndb
from google.appengine.api import images
from google.appengine.api import urlfetch

from webapp2_extras.auth import InvalidAuthIdError, InvalidPasswordError
from webapp2_extras import auth
from webapp2_extras import security

from base_api import ALittleCloserBaseService

from alittlecloser_api_messages import ConnectionListRequest
from alittlecloser_api_messages import ConnectionListResponse
from alittlecloser_api_messages import ConnectionAddRequest
from alittlecloser_api_messages import ConnectionAddResponse
from alittlecloser_api_messages import ConnectionDeleteRequest
from alittlecloser_api_messages import ConnectionDeleteResponse
from alittlecloser_api_messages import ConnectionUpdateRequest
from alittlecloser_api_messages import ConnectionUpdateResponse
from alittlecloser_api_messages import ConnectionRequest
from alittlecloser_api_messages import ConnectionResponse
from alittlecloser_api_messages import MediaJsonMessage
from alittlecloser_api_messages import MediaJsonFinalResponse

from alittlecloser_api_messages import SearchRequest
from alittlecloser_api_messages import SearchMessage
from alittlecloser_api_messages import SearchResponse
from alittlecloser_api_messages import SearchAddRequest
from alittlecloser_api_messages import SearchAddResponse
from alittlecloser_api_messages import SearchDeleteRequest
from alittlecloser_api_messages import SearchDeleteResponse

from alittlecloser_api_messages import CommentsListRequest
from alittlecloser_api_messages import CommentsListResponse
from alittlecloser_api_messages import CommentsAddRequest
from alittlecloser_api_messages import CommentsAddResponse
from alittlecloser_api_messages import CommentsDeleteRequest
from alittlecloser_api_messages import CommentsDeleteResponse

from alittlecloser_api_messages import BlobUploadListRequest
from alittlecloser_api_messages import BlobUploadListResponse

from alittlecloser_api_messages import HSLocationRequest
from alittlecloser_api_messages import HSLocationResponse
from alittlecloser_api_messages import HSLocationAddRequest
from alittlecloser_api_messages import HSLocationAddResponse

from alittlecloser_api_messages import LoginRequest
from alittlecloser_api_messages import LoginResponse

from web.models import Connection, PeopleThing, Comments, User, ApiKeys, Locations

CLIENT_ID = '787678794835.apps.googleusercontent.com'

if "SERVER_SOFTWARE" in os.environ:
    if os.environ['SERVER_SOFTWARE'].startswith('Dev'):
        from config.localhost import config

    elif os.environ['SERVER_SOFTWARE'].startswith('Google'):
        from config.production import config
else:
    from config.testing import config



@endpoints.api(name='alittlecloser', version='v1',
               description='A Little Closer API',
               allowed_client_ids=[CLIENT_ID, endpoints.API_EXPLORER_CLIENT_ID])
class ALittleCloserApi(ALittleCloserBaseService):
    """Class which defines alittlecloser API v1."""
    # Classes for login
    @endpoints.method(LoginRequest, LoginResponse,
                      path='login', http_method='POST',
                      name='login')
    def login(self, request):
        """Exposes an API endpoint to query for an upload URL.

        Args:


        Returns:

        """
        salt=config.get('salt')
        aes_key=config.get('aes_key')
        if not request.username:
            LoginResponse(message="Provide a username")
        username = request.username.lower()

        # try:
        if utils.is_email_valid(username):
            user = User.get_by_email(username)
            if user:
                auth_id = user.auth_ids[0]
            else:
                raise InvalidAuthIdError
        else:
            auth_id = "own:%s" % username
            user = User.get_by_auth_id(auth_id)

        password = request.password.strip()
        remember_me=False

        # Password to SHA512
        password = utils.hashing(password, salt)

        # Try to login user with password
        # Raises InvalidAuthIdError if user is not found
        # Raises InvalidPasswordError if provided password
        # doesn't match with specified user
        user = User.get_by_auth_id(auth_id)
        if not user:
            raise endpoints.BadRequestException('Password/Username Do Not Match')

        if not security.check_password_hash(password, user.password):
            raise endpoints.BadRequestException('Password/Username Do Not Match')

        else:
            self.user_apikey = ApiKeys.get_apikey_by_user_id(user.key.id()).key.id()

        return LoginResponse(apikey=self.user_apikey)







    #-------------------CONNECTION METHODS--------------------------------------
    @endpoints.method(ConnectionListRequest, ConnectionListResponse,
                      path='connections', http_method='GET',
                      name='connections.list')
    def connection_list(self, request):
        filter_dict = {}
        if request.apikey:
            self.apikey_model = self.lookup_api_key(request.apikey)
            if self.apikey_model is not None:
                self.apikey_model.total_calls += 1
                self.apikey_model.put()
                self.user_id = self.apikey_model.user_id
                self.user_key = User.get_user_by_id(self.user_id).key
                filter_dict['user_key'] = self.user_key

        self.curs = Cursor(urlsafe=request.cursor)
        #If the user does not specify the limit of results, use 20
        if not request.limit:
            request.limit = 20

        if request.created:
            filter_dict['created'] = request.created

        if request.updated:
            filter_dict['updated'] = request.updated

        if request.connection_stage:
            filter_dict['connection_stage'] = request.connection_stage

        if request.connection_type:
            filter_dict['connection_type'] = request.connection_type

        if request.loc_name:
            if request.loc_name != "all":
                filter_dict['loc_name'] = request.loc_name

        if request.user_name:
            filter_dict['user_name'] = request.user_name

        if request.title:
            filter_dict['title'] = request.title

        if request.type:
            filter_dict['type'] = request.type

        if request.personthing_id:
            filter_dict['personthing_key'] = PeopleThing.get_by_id(request.personthing_id).key

        self.all_connections, next_curs, more_results = Connection.get_connections(self.curs, request.limit, filter_dict)


        connects = []

        for entity in self.all_connections:
            if request.loc_name != "all":
                self.connection_response = entity.to_message(entity.media_binary)

            else:
                self.connection_response = entity.to_message_no_media()
            connects.append(self.connection_response)

        if more_results is True:
            self.cursor=next_curs.urlsafe()
        else:
            self.cursor="No More Results"
        return ConnectionListResponse(connections=connects, cursor = self.cursor, num_of_results = len(self.all_connections))


    @endpoints.method(ConnectionAddRequest, ConnectionAddResponse,
                      path='connections', http_method='POST',
                      name='connections.add')
    def connection_add(self, request):
        # Create New Connection DB Instance
        index = search.Index(name="alcindex_01")
        self.header_dict = self.parse_header(self.request_state.headers._headers)
        new_connection = Connection()
        search_document_dictionary = {}
        search_document_dictionary['title'] = None
        search_document_dictionary['loc_name'] = None
        search_document_dictionary['personthing_name'] = None
        search_document_dictionary['user_name'] = None
        search_document_dictionary['blog_title'] = None
        search_document_dictionary['type'] = None
        search_document_dictionary['latitude'] = None
        search_document_dictionary['longitude'] = None
        search_document_dictionary['body'] = None
        search_document_dictionary['summary'] = None
        search_document_dictionary['tags'] = None


        if request.apikey:
            self.apikey_model = ApiKeys.get_apikey_by_id(request.apikey)
            if self.apikey_model is None:
                return ConnectionAddResponse(message="the API key provided is no longer valid")
            else:
                self.user_model = User.get_user_by_id(self.apikey_model.user_id)
                self.model_current_posts = Connection.get_connections_by_user_id_status(self.user_model.key)
                new_connection.user_name = self.user_model.username
                new_connection.user_key = self.user_model.key
                self.apikey_model.total_calls += 1
                self.apikey_model.put()
                search_document_dictionary['user_name'] = self.user_model.name
        else:
            return ConnectionAddResponse(message="you must provide an API key")



        if self.model_current_posts and len(self.model_current_posts) > 4:
            return ConnectionAddResponse(message="user can only have 5 pending requests: %s" % request.apikey)

        # if len(Connection.get_connection_by_title(request.title)) > 0:
        #     return ConnectionAddResponse(message="title already exists %s" % request.title)

        if request.personthing_id:
            self.personthing_model = PeopleThing.get_person_by_id(request.personthing_id)
            new_connection.personthing_name = self.personthing_model.name
            new_connection.personthing_key = self.personthing_model.key
            search_document_dictionary['personthing_name'] = self.personthing_model.name

        #If the API only provides a name, I will create a personthing
        elif request.personthing_name:
            new_personthing = PeopleThing()
            new_personthing.name = request.personthing_name
            new_connection.personthing_name = new_personthing.name
            new_connection.personthing_key = new_personthing.put()
            search_document_dictionary['personthing_name'] = new_personthing.name


        if request.media:
            new_connection.media = request.media
            # Add the API object for the media
            self.media_response_full = []
            self.json_gen = self.iterload(request.media)
            self.media_response = []
            for media_item in self.json_gen['results']:
                self.media_response.append(MediaJsonMessage(width = int(media_item['width']),
                                                            height = int(media_item['height']),
                                                            filetype = media_item['filetype'],
                                                            file_cat = media_item['file_cat'],
                                                            blob_key = images.get_serving_url(media_item['blobstore_key'])))
            self.media_response_full.append(MediaJsonFinalResponse(media_item_message=self.media_response,
                                                                   filename = self.json_gen['filename']))
            new_connection.media_binary = self.media_response_full


        if request.latitude and request.longitude:
            #temporarily storing as lat, lng, and geopt because I am unsure of how to interact with it later
            new_connection.latitude = request.latitude
            new_connection.longitude = request.longitude
            new_connection.loc_geopt = ndb.GeoPt(float(request.latitude), float(request.longitude))

        new_connection.type = request.type
        new_connection.title = request.title
        new_connection.summary = request.summary
        new_connection.primary_media = request.primary_media
        new_connection.request_reason = request.request_reason
        new_connection.private_loc = request.private_location
        new_connection.personalized_message = request.personalized_message
        new_connection.uastring = self.header_dict['user-agent']
        new_connection.ip = self.request_state.remote_address




        new_connection_key = new_connection.put()

        search_document_dictionary['type'] = request.type
        search_document_dictionary['title'] = request.title
        search_document_dictionary['summary'] = request.summary
        search_document_dictionary['latitude'] = request.latitude
        search_document_dictionary['longitude'] = request.longitude
        search_document_dictionary['connection_id'] = str(new_connection_key.id())
        new_search_doc_id = self.search_doc_create(search_document_dictionary, index)

        short = new_connection_key.get()
        short_url = 'http://www.bealittlecloser.com/map?node_id=%s&lat=%s&lng=%s&zoom=15' % (new_connection_key.id(), request.latitude, request.longitude)
        short.social_media_json = self.create_short_url(short_url)
        short.put()

        return ConnectionAddResponse(message="successfully added connection", new_connection_id = new_connection_key.id())


    @endpoints.method(ConnectionUpdateRequest, ConnectionUpdateResponse,
                      path='connections', http_method='PUT',
                      name='connections.update')
    def connection_update(self, request):
        # Create New Connection DB Instance
        self.header_dict = self.parse_header(self.request_state.headers._headers)

        if request.apikey:
            self.apikey_model = ApiKeys.get_apikey_by_id(request.apikey)
            if self.apikey_model is None:
                return ConnectionUpdateResponse(message="the API key provided is no longer valid")
            else:
                self.update_connection_model = Connection.get_connection_by_id(request.connection_id)
                self.user_model = User.get_user_by_id(self.apikey_model.user_id)
                self.update_connection_model.user_name = self.user_model.name
                self.update_connection_model.user_key = self.user_model.key
                self.apikey_model.total_calls += 1
                self.apikey_model.put()
        else:
            return ConnectionAddResponse(message="you must provide an API key")


        if self.update_connection_model is None:
            return ConnectionUpdateResponse(message="ID not found: %s" % request.connection_id)

        if request.personthing_id:
            request.personthing_name = self.personthing_model.name
            self.update_connection_model.personthing_key = self.personthing_model.key

        if request.media:
            self.update_connection_model.media = request.media

        if request.type is not None:
            self.update_connection_model.type = request.type
        if request.title is not None:
            self.update_connection_model.title = request.title
        if request.summary is not None:
            self.update_connection_model.summary = request.summary
        if request.body is not None:
            self.update_connection_model.body = request.body
        if request.primary_media is not None:
            self.update_connection_model.primary_media = request.primary_media
        if request.connection_stage is not None:
            self.update_connection_model.connection_stage = request.connection_stage
        if request.personthing_name is not None:
            self.update_connection_model.personthing_name = request.personthing_name
        if request.request_reason is not None:
            self.update_connection_model.request_reason = request.request_reason
        if request.private_location is not None:
            self.update_connection_model.private_loc = request.private_location
        if request.personalized_message is not None:
            self.update_connection_model.personalized_message = request.personalized_message
        self.update_connection_model.uastring = self.header_dict['user-agent']
        self.update_connection_model.ip = self.request_state.remote_address
        update_connection_key = self.update_connection_model.put()

        return ConnectionUpdateResponse(message="successfully updated connection", update_connection_id = update_connection_key.id())


    @endpoints.method(ConnectionDeleteRequest, ConnectionDeleteResponse,
                      path='connections', http_method='DELETE',
                      name='connections.delete')
    def connection_delete(self, request):
        index = search.Index(name="alcindex_01")
        if request.apikey:
            self.apikey_model = ApiKeys.get_apikey_by_id(request.apikey)
            if self.apikey_model is None:
                return ConnectionDeleteResponse(message="the API key provided is no longer valid")
            else:
                self.apikey_model.total_calls += 1
                self.apikey_model.put()
        else:
            return ConnectionDeleteResponse(message="you must provide an API key")

        if request.connection_id:
            self.connection_model = Connection.get_connection_by_id(request.connection_id)
        else:
            return ConnectionDeleteResponse(message="connection id required")

        if self.connection_model is not None:
            #DELETE SEARCH INDEX RECORD
            results = index.search(search.Query('connection_id:'+request.connection_id+''))
            self.connection_model.key.delete()
            index.delete(results.results[0].doc_id)
            return ConnectionDeleteResponse(message="successfully deleted: %s" % request.connection_id)
        else:
            return ConnectionDeleteResponse(message="ID not found: %s" % request.connection_id)


    #-------------------BLOB METHODS--------------------------------------
    @endpoints.method(BlobUploadListRequest, BlobUploadListResponse,
                      path='blob', http_method='GET',
                      name='blob.getuploadurl')
    def upload_url(self, request):
        self.upload_url = blobstore.create_upload_url(request.upload_path, gs_bucket_name='alittleclose_media')
        return BlobUploadListResponse(upload_url=self.upload_url)


    #-------------------CONNECTION METHOD--------------------------------------
    @endpoints.method(ConnectionRequest, ConnectionResponse,
                      path='connection', http_method='GET',
                      name='connection.getdetails')
    def get_connection(self, request):
        if request.apikey:
            self.apikey_model = self.lookup_api_key(request.apikey)
            if self.apikey_model is not None:
                self.apikey_model.total_calls += 1
                self.apikey_model.put()

        if request.connection_id:
            self.connection_model = Connection.get_connection_by_id(request.connection_id)
        else:
            return ConnectionResponse(message="connection id required")
        if self.connection_model is not None:
            if self.connection_model.media.startswith('{"filename":'):
                result_list = self.connection_model.media.split('{"filename":')
                self.media_response_full = []
                for media_list_item in result_list:
                    if media_list_item != "":
                        try:
                            if media_list_item[-1:] == ",":
                                self.json_loads = json.loads('{"filename":'+media_list_item[:-1])
                            else:
                                self.json_loads = json.loads('{"filename":'+media_list_item)

                            self.media_response = []
                            self.filename = self.json_loads['filename']
                            for media_item in self.json_loads['results']:
                                self.media_response.append(MediaJsonMessage(width = int(media_item['width']),
                                                 height = int(media_item['height']),
                                                 filetype = media_item['filetype'],
                                                 file_cat = media_item['file_cat'],
                                                 blob_key = images.get_serving_url(media_item['blobstore_key'])))
                            self.media_response_full.append(MediaJsonFinalResponse(media_item_message=self.media_response,
                                                                                   filename = self.filename))
                        except:
                            if media_list_item[-1:] == ",":
                                self.json_loads = json.loads(media_list_item[:-1])
                            else:
                                self.json_loads = json.loads(media_list_item)

                            self.media_response = []
                            self.filename = self.json_loads['filename']
                            for media_item in self.json_loads['results']:
                                self.media_response.append(MediaJsonMessage(width = int(media_item['width']),
                                                                            height = int(media_item['height']),
                                                                            filetype = media_item['filetype'],
                                                                            file_cat = media_item['file_cat'],
                                                                            blob_key = images.get_serving_url(media_item['blobstore_key'])))
                            self.media_response_full.append(MediaJsonFinalResponse(media_item_message=self.media_response,
                                                                                   filename = self.filename))


            else:
                result_list = self.connection_model.media.split('{"results":')
                self.media_response_full = []
                for media_list_item in result_list:
                    if media_list_item != "":
                        try:
                            if media_list_item[-1:] == ",":
                                self.json_loads = json.loads('{"results":'+media_list_item[:-1])
                            else:
                                self.json_loads = json.loads('{"results":'+media_list_item)

                            self.media_response = []
                            self.filename = self.json_loads['filename']
                            for media_item in self.json_loads['results']:
                                self.media_response.append(MediaJsonMessage(width = int(media_item['width']),
                                                                            height = int(media_item['height']),
                                                                            filetype = media_item['filetype'],
                                                                            file_cat = media_item['file_cat'],
                                                                            blob_key = images.get_serving_url(media_item['blobstore_key'])))
                            self.media_response_full.append(MediaJsonFinalResponse(media_item_message=self.media_response,
                                                                                   filename = self.filename))
                        except:
                            if media_list_item[-1:] == ",":
                                self.json_loads = json.loads(media_list_item[:-1])
                            else:
                                self.json_loads = json.loads(media_list_item)

                            self.media_response = []
                            self.filename = self.json_loads['filename']
                            for media_item in self.json_loads['results']:
                                self.media_response.append(MediaJsonMessage(width = int(media_item['width']),
                                                                            height = int(media_item['height']),
                                                                            filetype = media_item['filetype'],
                                                                            file_cat = media_item['file_cat'],
                                                                            blob_key = images.get_serving_url(media_item['blobstore_key'])))
                            self.media_response_full.append(MediaJsonFinalResponse(media_item_message=self.media_response,
                                                                                   filename = self.filename))


            self.connection_response = self.connection_model.to_indiv_message(self.media_response_full)
            return ConnectionResponse(connection=self.connection_response)
        else:
            return ConnectionResponse(message="ID not found: %s" % request.connection_id)


    #-------------------SEARCH METHODS--------------------------------------
    @endpoints.method(SearchRequest, SearchResponse,
                      path='search', http_method='GET',
                      name='search.query')
    def search_response(self, request):
        self.cursor = search.Cursor()

        index = search.Index(name="alcindex_01")
        search_dict = {}
        search_string = ""
        #If the user does not specify the limit of results, use 20
        if not request.limit:
            request.limit = 20

        if request.created:
            search_dict['created'] = request.created

        if request.updated:
            search_dict['updated'] = request.updated

        if request.loc_name:
            search_dict['loc_name_substr'] = request.loc_name

        if request.user_name:
            search_dict['user_name_substr'] = request.user_name

        if request.title:
            search_dict['title_substr'] = request.title

        if request.blog_title:
            search_dict['blog_title_substr'] = request.blog_title

        if request.type:
            search_dict['type_substr'] = request.type

        if request.body:
            search_dict['body_substr'] = request.body

        if request.summary:
            search_dict['summary_substr'] = request.summary

        if request.tags:
            search_dict['tags_substr'] = request.tags

        if request.personthing_name:
            search_dict['personthing_name_substr'] = request.personthing_name

        if request.latitude:
            search_dict['geofield'] = "distance(geofield, geopoint(%s, %s))<%s" % (request.latitude, request.longitude, request.geo_distance)

        if request.q:
            self.q = request.q
        else:
            self.q = None

        if request.cursor:
            self.cursor = search.Cursor(web_safe_string=request.cursor)


        self.and_int = 0
        search_string = ""

        if self.and_int == 0 and self.q:
            search_string = "%s" % (self.q)
            self.and_int = 1

        for k,v in search_dict.iteritems():
            if self.and_int == 0 and not self.q:
                if k == 'geofield':
                    search_string = "%s" % (v)
                else:
                    search_string = "%s=%s" % (k, v)
                self.and_int = 1
            else:
                if k == 'geofield':
                    search_string = "%s" % (v)
                else:
                    search_string = "%s AND %s=%s" % (search_string, k, v)


        try:
            # build options and query
            options = search.QueryOptions(cursor=self.cursor)
            query = search.Query(query_string=search_string, options=options)

            # search at least once
            result = index.search(query)
            self.number_retrieved = result.number_found
            self.cursor = result.cursor

            if self.number_retrieved > 0:
            # ... process the matched docs
                self.results_message = [self.search_message_handler(entity) for entity in result.results]

            else:
                return SearchResponse(message = "No results")

        except search.Error:
            logging.exception('Search failed')

        return SearchResponse(search=self.results_message, cursor=self.cursor, num_of_results = self.number_retrieved)

    def search_message_handler(self, result):
        search_response_dict = {}
        search_response_dict['title'] = None
        search_response_dict['loc_name'] = None
        search_response_dict['personthing_name'] = None
        search_response_dict['user_name'] = None
        search_response_dict['blog_title'] = None
        search_response_dict['type'] = None
        search_response_dict['latitude'] = None
        search_response_dict['longitude'] = None
        search_response_dict['body'] = None
        search_response_dict['summary'] = None
        search_response_dict['tags'] = None
        search_response_dict['connection_id'] = None

        for field in result.fields:
            search_response_dict[field.name] = field.value

        return SearchMessage(title=search_response_dict['title'],
                             loc_name=search_response_dict['loc_name'],
                             personthing_name=search_response_dict['personthing_name'],
                             user_name=search_response_dict['user_name'],
                             blog_title=search_response_dict['blog_title'],
                             type=search_response_dict['type'],
                             latitude=search_response_dict['latitude'],
                             longitude=search_response_dict['longitude'],
                             body=search_response_dict['body'],
                             summary=search_response_dict['summary'],
                             tags=search_response_dict['tags'],
                             connection_id=search_response_dict['connection_id'])

    @endpoints.method(SearchAddRequest, SearchAddResponse,
                      path='search', http_method='POST',
                      name='search.add')
    def search_add(self, request):
        # Create New Connection DB Instance
        self.header_dict = self.parse_header(self.request_state.headers._headers)
        index = search.Index(name="alcindex_01")

        try:
            self.user_key = User.get_user_by_id(request.user_id)
        except:
            return SearchAddResponse(message="user_id is a required field")

        search_document_dictionary = {}

        if request.user_id:
            self.user_model = User.get_user_by_id(request.user_id)
            if self.user_model is not None:
                search_document_dictionary['user_name'] = self.user_model.name
            else:
                return SearchAddResponse(message="provided user id did not match")
        else:
            search_document_dictionary['user_name'] = None

        if request.personthing_id:
            self.personthing_model = PeopleThing.get_person_by_id(request.personthing_id)
            search_document_dictionary['personthing_name'] = self.personthing_model.name

        else:
            search_document_dictionary['personthing_name'] = None

        search_document_dictionary['type'] = request.type
        search_document_dictionary['title'] = request.title
        search_document_dictionary['blog_title'] = request.blog_title
        search_document_dictionary['summary'] = request.summary
        search_document_dictionary['tags'] = request.tags
        search_document_dictionary['latitude'] = request.latitude
        search_document_dictionary['longitude'] = request.longitude
        search_document_dictionary['body'] = request.body
        new_search_doc_id = self.search_doc_create(search_document_dictionary, index)

        return SearchAddResponse(message="successfully added connection", new_search_id = new_search_doc_id[0].id)


    @endpoints.method(SearchDeleteRequest, SearchDeleteResponse,
                      path='search', http_method='DELETE',
                      name='search.delete')
    def search_delete(self, request):
        index = search.Index(name="alcindex_01")

        # Fetch a single document by its doc_id
        self.doc = index.get(request.search_doc_id)
        if self.doc is not None:
            index.delete(request.search_doc_id)
            return SearchDeleteResponse(message="successfully deleted: %s" % request.search_doc_id)
        else:
            return SearchDeleteResponse(message="ID not found: %s" % request.search_doc_id)


    #-------------------COMMENT METHODS--------------------------------------
    @endpoints.method(CommentsListRequest, CommentsListResponse,
                      path='comments', http_method='GET',
                      name='comments.list')
    def comments_list(self, request):
        filter_dict = {}
        self.curs = Cursor(urlsafe=request.cursor)
        #If the user does not specify the limit of results, use 20
        if not request.limit:
            request.limit = 20

        if request.created:
            filter_dict['created'] = request.created

        if request.updated:
            filter_dict['updated'] = request.updated

        if request.tags:
            filter_dict['tags'] = request.connection_stage

        if request.title:
            filter_dict['title'] = request.title

        if request.user_id:
            filter_dict['user_key'] = User.get_user_by_id(request.user_id).key

        if request.personthing_id:
            filter_dict['personthing_key'] = PeopleThing.get_person_by_id(request.personthing_id).key

        if request.connection_id:
            filter_dict['connection_key'] = Connection.get_connection_by_id(request.connection_id).key

        self.all_comments, next_curs, more_results = Comments.get_comments(self.curs, request.limit, filter_dict)
        comments = [comment.to_comment_message() for comment in self.all_comments]
        if more_results is True:
            self.cursor=next_curs.urlsafe()
        else:
            self.cursor="No More Results"
        return CommentsListResponse(comments=comments, cursor = self.cursor, num_of_results = len(self.all_comments))


    @endpoints.method(CommentsAddRequest, CommentsAddResponse,
                      path='comments', http_method='POST',
                      name='comments.add')
    def comments_add(self, request):
        if request.apikey:
            self.apikey_model = ApiKeys.get_apikey_by_id(request.apikey)
            if self.apikey_model is None:
                return CommentsAddResponse(message="the API key provided is no longer valid")
            else:
                new_comment = Comments()
                self.user_model = User.get_user_by_id(self.apikey_model.user_id)
                self.model_current_posts = Connection.get_connections_by_user_id_status(self.user_model.key)
                new_comment.user_name = self.user_model.username
                new_comment.user_key = self.user_model.key
                self.apikey_model.total_calls += 1
                self.apikey_model.put()

        else:
            return ConnectionAddResponse(message="you must provide an API key")

        self.header_dict = self.parse_header(self.request_state.headers._headers)

        # if len(Connection.get_connection_by_title(request.title)) > 0:
        #     return CommentsAddResponse(message="title already exists %s" % request.title)

        if request.personthing_id:
            self.personthing_model = PeopleThing.get_person_by_id(request.personthing_id)
            new_comment.personthing_key = self.personthing_model.key
            new_comment.personthing_name = self.personthing_model.name

        if request.user_id:
            self.user_model = User.get_user_by_id(request.user_id)
            new_comment.user_key = self.user_model.key
            new_comment.user_name = self.user_model.name

        if request.connection_id:
            try:
                self.connection_model = Connection.get_connection_by_id(request.connection_id)
                new_comment.connection_key = self.connection_model.key
                new_comment.connection_title = self.connection_model.title
            except:
                return CommentsAddResponse(message="Connection ID not valid: %s" % request.connection_id)


        if request.media:
            new_comment.media = request.media

        new_comment.post_type = request.post_type
        new_comment.title = request.title
        new_comment.tags = request.tags
        new_comment.body = request.body

        new_comment.uastring = self.header_dict['user-agent']
        new_comment.ip = self.request_state.remote_address
        new_blog_key = new_comment.put()

        return CommentsAddResponse(message="successfully added comment", comment_id = new_blog_key.id())


    @endpoints.method(CommentsDeleteRequest, CommentsDeleteResponse,
                      path='comments', http_method='DELETE',
                      name='comments.delete')
    def comment_delete(self, request):
        self.post_model = Comments.get_comment_by_id(request.post_id)
        if self.post_model is not None:
            self.post_model.key.delete()
            return CommentsDeleteResponse(message="successfully deleted: %s" % request.post_id)
        else:
            return CommentsDeleteResponse(message="ID not found: %s" % request.post_id)


    def parse_header(self, headers):
        header_dict = {}
        for header_item in headers:
            header_dict[header_item[0]] = header_item[1]
        return header_dict

    #-------------------TRAVELING LOCATION METHODS--------------------------------------
    @endpoints.method(HSLocationRequest, HSLocationResponse,
                      path='locations', http_method='GET',
                      name='locations.list')
    def location_list(self, request):
        filter_dict = {}
        if request.apikey:
            self.apikey_model = self.lookup_api_key(request.apikey)
            if self.apikey_model is not None:
                self.apikey_model.total_calls += 1
                self.apikey_model.put()

        self.curs = Cursor(urlsafe=request.cursor)
        #If the user does not specify the limit of results, use 20
        if request.type:
            filter_dict['type'] = request.type
        if request.limit:
            limit = request.limit
        else:
            limit = 600

        self.all_locations, next_curs, more_results = Locations.get_locations(self.curs, limit, filter_dict)
        self.final_locations = [location.to_location_message() for location in self.all_locations]


        if more_results is True:
            self.cursor=next_curs.urlsafe()
        else:
            self.cursor="No More Results"
        return HSLocationResponse(locations=self.final_locations, cursor = self.cursor, num_of_results = len(self.final_locations))


    @endpoints.method(HSLocationAddRequest, HSLocationAddResponse,
                      path='locations', http_method='POST',
                      name='locations.add')
    def location_add(self, request):
        # Create New Connection DB Instance
        index = search.Index(name="alcindex_01")
        self.header_dict = self.parse_header(self.request_state.headers._headers)
        new_place = Locations()

        if request.apikey:
            self.apikey_model = ApiKeys.get_apikey_by_id(request.apikey)
            if self.apikey_model is None:
                return ConnectionAddResponse(message="the API key provided is no longer valid")
            else:
                self.apikey_model.total_calls += 1
                self.apikey_model.put()

        else:
            return ConnectionAddResponse(message="you must provide an API key")


        if request.latitude and request.longitude:
            #temporarily storing as lat, lng, and geopt because I am unsure of how to interact with it later
            new_place.latitude = request.latitude
            new_place.longitude = request.longitude
            new_place.loc_geopt = ndb.GeoPt(float(request.latitude), float(request.longitude))

        new_place.title = request.title
        new_place.loc_name = request.loc_name
        new_place.type = request.type
        new_place.uastring = self.header_dict['user-agent']
        new_place.ip = self.request_state.remote_address
        new_place_key = new_place.put()

        return HSLocationAddResponse(message="successfully added location", new_connection_id = new_place_key.id())


    def create_short_url(self, long_url):

        long_url = long_url.replace("&","%26")
        longer_url = "http://is.gd/create.php?format=simple&url=%s" % long_url
        response = urlfetch.fetch(longer_url)
        if response.status_code == 200:
            return response.content
        raise Exception("Call failed. Status code %s. Body %s",
                        response.status_code, response.content)

    def iterload(self, string_or_fp, cls=json.JSONDecoder, **kwargs):
        if isinstance(string_or_fp, file):
            string = string_or_fp.read()
        else:
            string = str(string_or_fp)

        decoder = cls(**kwargs)
        idx = WHITESPACE.match(string, 0).end()
        while idx < len(string):
            obj, end = decoder.raw_decode(string, idx)
            # yield obj
            return obj
            idx = WHITESPACE.match(string, end).end()


APPLICATION = endpoints.api_server([ALittleCloserApi],
                                   restricted=False)