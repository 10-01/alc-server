__author__ = 'hstrauss'

from google.appengine.ext import endpoints
from protorpc import remote
from google.appengine.api import search
import webapp2
from lib import utils
from web import models
from webapp2_extras import auth
from webapp2_extras import sessions

class ALittleCloserBaseService(remote.Service):
    def search_doc_create(self, search_doc_dict, index):
        search_doc_fields = []
        if search_doc_dict['title']:
            search_doc_fields.append(search.TextField(name= 'title', value=search_doc_dict['title']))
            search_doc_fields.append(search.TextField(name= 'title_substr', value=self.build_suggestions(search_doc_dict['title'])))

        if search_doc_dict['personthing_name']:
            search_doc_fields.append(search.TextField(name= 'personthing_name', value=search_doc_dict['personthing_name']))
            search_doc_fields.append(search.TextField(name= 'personthing_name_substr', value=self.build_suggestions(search_doc_dict['personthing_name'])))

        if search_doc_dict['user_name']:
            search_doc_fields.append(search.TextField(name= 'user_name', value=search_doc_dict['user_name']))
            search_doc_fields.append(search.TextField(name= 'user_name_substr', value=self.build_suggestions(search_doc_dict['user_name'])))

        if search_doc_dict['type']:
            search_doc_fields.append(search.TextField(name= 'type', value=search_doc_dict['type']))
            search_doc_fields.append(search.TextField(name= 'type_substr', value=self.build_suggestions(search_doc_dict['type'])))

        if search_doc_dict['blog_title']:
            search_doc_fields.append(search.TextField(name= 'blog_title', value=search_doc_dict['blog_title']))
            search_doc_fields.append(search.TextField(name= 'blog_title_substr', value=self.build_suggestions(search_doc_dict['blog_title'])))

        if search_doc_dict['summary']:
            search_doc_fields.append(search.TextField(name= 'summary', value=search_doc_dict['summary']))
            search_doc_fields.append(search.TextField(name= 'summary_substr', value=self.build_suggestions(search_doc_dict['summary'])))

        if search_doc_dict['body']:
            search_doc_fields.append(search.TextField(name= 'body', value=search_doc_dict['body']))
            search_doc_fields.append(search.TextField(name= 'body_substr', value=self.build_suggestions(search_doc_dict['body'])))


        if search_doc_dict['tags']:
            search_doc_fields.append(search.TextField(name= 'tags', value=search_doc_dict['tags']))
            search_doc_fields.append(search.TextField(name= 'tags_substr', value=self.build_suggestions(search_doc_dict['tags'])))

        if search_doc_dict['latitude']:
            search_doc_fields.append(search.GeoField(name= 'geofield', value=search.GeoPoint(search_doc_dict['latitude'], search_doc_dict['longitude'])))
            search_doc_fields.append(search.NumberField(name= 'latitude', value=search_doc_dict['latitude']))
            search_doc_fields.append(search.NumberField(name= 'longitude', value=search_doc_dict['longitude']))

        if search_doc_dict['connection_id']:
            search_doc_fields.append(search.TextField(name= 'connection_id', value=search_doc_dict['connection_id']))

        docset = search.Document(
        fields=search_doc_fields)
        print search_doc_fields
        return index.put(docset)

    """ Takes a sentence and returns the set of all possible prefixes for each word.
    For instance "hello world" becomes "h he hel hell hello w wo wor worl world" """
    def build_suggestions(self, str):
        suggestions = []
        suggestions.append(str)
        for word in str.split():
            prefix = ""
            for letter in word:
                prefix += letter
                suggestions.append(prefix)
        return ' '.join(suggestions)

    def lookup_api_key(self,apikey):
        return models.ApiKeys.get_apikey_by_id(apikey)


