#Created using IntelliJ IDEA.

from protorpc import messages
from protorpc import message_types

class MediaJsonMessage(messages.Message):
    width = messages.IntegerField(1)
    height = messages.IntegerField(2)
    filetype = messages.StringField(3)
    blob_key = messages.StringField(4)
    file_cat = messages.StringField(5)

class MediaJsonFinalResponse(messages.Message):
    media_item_message = messages.MessageField(MediaJsonMessage, 1, repeated=True)
    filename = messages.StringField(2)

# CLASSES FOR GETTING CONNECTIONS
class ConnectionListRequest(messages.Message):
    """ProtoRPC message definition to represent a scores query."""
    limit = messages.IntegerField(1)
    cursor = messages.StringField(2)
    created = message_types.DateTimeField(3)
    updated = message_types.DateTimeField(4)
    connection_stage = messages.IntegerField(5)
    connection_type = messages.StringField(6)
    loc_name = messages.StringField(7)
    user_name = messages.StringField(8)
    title = messages.StringField(9)
    type = messages.StringField(10)
    personthing_id = messages.StringField(11)
    apikey = messages.IntegerField(12)

class ConnectionResponseMessage(messages.Message):
    """ProtoRPC message definition to represent a score that is stored."""
    title = messages.StringField(1)
    type = messages.StringField(2)
    blog_url=messages.StringField(3)
    completed = messages.BooleanField(4)
    completion_date = message_types.DateTimeField(5)
    connection_stage = messages.IntegerField(6)
    connection_type = messages.StringField(7)
    latitude = messages.FloatField(8)
    longitude = messages.FloatField(9)
    loc_name = messages.StringField(10)
    marker_color = messages.StringField(11)
    marker_size = messages.StringField(12)
    marker_symbol = messages.StringField(13)
    media = messages.MessageField(MediaJsonFinalResponse, 14, repeated=True)
    user_id =  messages.IntegerField(15)
    user_name =  messages.StringField(16)
    user_picture = messages.StringField(17)
    personthing_id = messages.StringField(18)
    personthing_name = messages.StringField(19)
    primary_media = messages.StringField(20)
    summary = messages.StringField(21)
    req_reason = messages.StringField(22)
    social_media_json = messages.StringField(23)
    created = message_types.DateTimeField(24)
    updated = message_types.DateTimeField(25)
    id = messages.IntegerField(26)



class ConnectionListResponse(messages.Message):
    """ProtoRPC message definition to represent a list of stored scores."""
    connections = messages.MessageField(ConnectionResponseMessage, 1, repeated=True)
    cursor = messages.StringField(2)
    num_of_results = messages.IntegerField(3)


# CLASSES FOR ADDING CONNECTIONS
class ConnectionAddRequest(messages.Message):
    """ProtoRPC message definition to represent a scores query."""

    # USER ENTERED
    type = messages.StringField(1)
    title = messages.StringField(2)
    summary = messages.StringField(3)
    personthing_name = messages.StringField(4)
    request_reason = messages.StringField(5)
    private_location = messages.StringField(6)
    personalized_message = messages.StringField(7)
    personthing_id = messages.IntegerField(8)
    media = messages.StringField(9)
    apikey = messages.IntegerField(10)
    latitude = messages.FloatField(11)
    longitude = messages.FloatField(12)
    primary_media = messages.StringField(13)

class ConnectionAddMessage(messages.Message):
    """ProtoRPC message definition to represent a score that is stored."""
    status = messages.StringField(1)

class ConnectionAddResponse(messages.Message):
    """ProtoRPC message definition to represent a scores query."""
    message = messages.StringField(1)
    new_connection_id = messages.IntegerField(2)



# CLASSES FOR UPDATING CONNECTIONS
class ConnectionUpdateRequest(messages.Message):
    """ProtoRPC message definition to represent a scores query."""
    type = messages.StringField(1)
    title = messages.StringField(2)
    summary = messages.StringField(3)
    personthing_name = messages.StringField(4)
    request_reason = messages.StringField(5)
    private_location = messages.StringField(6)
    personalized_message = messages.StringField(7)
    personthing_id = messages.IntegerField(8)
    media = messages.StringField(9)
    connection_id = messages.StringField(10)
    apikey = messages.IntegerField(11)
    connection_stage = messages.IntegerField(12)
    body = messages.StringField(13)
    primary_media = messages.StringField(14)

class ConnectionUpdateResponse(messages.Message):
    """ProtoRPC message definition to represent a scores query."""
    update_connection_id = messages.IntegerField(1)
    message = messages.StringField(2)


# CLASSES FOR DELETE CONNECTIONS
class ConnectionDeleteRequest(messages.Message):
    """ProtoRPC message definition to represent a scores query."""
    connection_id = messages.StringField(1)
    apikey = messages.IntegerField(2)

class ConnectionDeleteResponse(messages.Message):
    """ProtoRPC message definition to represent a scores query."""
    message = messages.StringField(1)


# CLASSES FOR SEARCH
class SearchRequest(messages.Message):
    """ProtoRPC message definition to represent a scores query."""
    limit = messages.IntegerField(1)
    created = message_types.DateTimeField(2)
    updated = message_types.DateTimeField(3)
    loc_name = messages.StringField(4)
    personthing_name = messages.StringField(5)
    user_name = messages.StringField(6)
    title = messages.StringField(7)
    blog_title = messages.StringField(8)
    type = messages.StringField(9)
    latitude = messages.StringField(10)
    longitude = messages.StringField(11)
    body = messages.StringField(12)
    summary = messages.StringField(13)
    tags = messages.StringField(14)
    q = messages.StringField(15)
    cursor = messages.StringField(16)
    geo_distance = messages.StringField(17)

class SearchMessage(messages.Message):
    """ProtoRPC message definition to represent a score that is stored."""
    limit = messages.IntegerField(1)
    created = message_types.DateTimeField(2)
    updated = message_types.DateTimeField(3)
    loc_name = messages.StringField(4)
    personthing_name = messages.StringField(5)
    user_name = messages.StringField(6)
    title = messages.StringField(7)
    blog_title = messages.StringField(8)
    type = messages.StringField(9)
    latitude = messages.FloatField(10)
    longitude = messages.FloatField(11)
    body = messages.StringField(12)
    summary = messages.StringField(13)
    tags = messages.StringField(14)
    connection_id = messages.StringField(15)



class SearchResponse(messages.Message):
    """ProtoRPC message definition to represent a list of stored scores."""
    search = messages.MessageField(SearchMessage, 1, repeated=True)
    cursor = messages.StringField(2)
    num_of_results = messages.IntegerField(3)
    message = messages.StringField(4)


# CLASSES FOR ADDING CONNECTIONS
class SearchAddRequest(messages.Message):
    """ProtoRPC message definition to represent a scores query."""

    # USER ENTERED
    created = message_types.DateTimeField(1)
    loc_name = messages.StringField(2)
    personthing_name = messages.StringField(3)
    user_name = messages.StringField(4)
    title = messages.StringField(5)
    blog_title = messages.StringField(6)
    type = messages.StringField(7)
    latitude = messages.FloatField(8)
    longitude = messages.FloatField(9)
    body = messages.StringField(10)
    summary = messages.StringField(11)
    tags = messages.StringField(12)
    user_id = messages.StringField(13)
    personthing_id = messages.StringField(14)


class SearchAddResponse(messages.Message):
    """ProtoRPC message definition to represent a scores query."""
    message = messages.StringField(1)
    new_search_id = messages.StringField(2)



# CLASSES FOR DELETE CONNECTIONS
class SearchDeleteRequest(messages.Message):
    """ProtoRPC message definition to represent a scores query."""
    search_doc_id = messages.StringField(1)

class SearchDeleteResponse(messages.Message):
    """ProtoRPC message definition to represent a scores query."""
    message = messages.StringField(1)



# CLASSES FOR BLOB STORE
class BlobUploadListRequest(messages.Message):
    """ProtoRPC message definition to represent a scores query."""
    upload_path = messages.StringField(1)

class BlobUploadListResponse(messages.Message):
    """ProtoRPC message definition to represent a list of stored scores."""
    upload_url = messages.StringField(1)


# CLASSES FOR CONNECTION
class ConnectionRequest(messages.Message):
    """ProtoRPC message definition to represent a scores query."""
    connection_id = messages.IntegerField(1)
    apikey = messages.IntegerField(2)

class SingleConnectionReponseMessage(messages.Message):
    """ProtoRPC message definition to represent a score that is stored."""
    title = messages.StringField(1)
    type = messages.StringField(2)
    blog_url=messages.StringField(3)
    completed = messages.BooleanField(4)
    completion_date = message_types.DateTimeField(5)
    connection_stage = messages.IntegerField(6)
    connection_type = messages.StringField(7)
    latitude = messages.FloatField(8)
    longitude = messages.FloatField(9)
    loc_name = messages.StringField(10)
    marker_color = messages.StringField(11)
    marker_size = messages.StringField(12)
    marker_symbol = messages.StringField(13)
    media = messages.MessageField(MediaJsonFinalResponse, 14, repeated=True)
    user_id =  messages.IntegerField(15)
    user_name =  messages.StringField(16)
    user_picture = messages.StringField(17)
    personthing_id = messages.StringField(18)
    personthing_name = messages.StringField(19)
    primary_media = messages.StringField(20)
    summary = messages.StringField(21)
    req_reason = messages.StringField(22)
    social_media_json = messages.StringField(23)
    created = message_types.DateTimeField(24)
    updated = message_types.DateTimeField(25)
    id = messages.IntegerField(26)
    body = messages.StringField(27)

class ConnectionResponse(messages.Message):
    """ProtoRPC message definition to represent a list of stored scores."""
    connection = messages.MessageField(SingleConnectionReponseMessage, 1)
    message = messages.StringField(2)



# CLASSES FOR GETTING COMMENTS
class CommentsListRequest(messages.Message):
    """ProtoRPC message definition to represent a scores query."""
    limit = messages.IntegerField(1)
    cursor = messages.StringField(2)
    tags = messages.StringField(3)
    title = messages.StringField(4)
    connection_id =messages.StringField(5)
    user_id = messages.StringField(6)
    personthing_id = messages.StringField(7)
    created = message_types.DateTimeField(8)
    updated = message_types.DateTimeField(9)

class CommentsResponseMessage(messages.Message):
    """ProtoRPC message definition to represent a score that is stored."""
    title = messages.StringField(1)
    post_type = messages.StringField(2)
    body = messages.StringField(3)
    tags = messages.StringField(4)
    media = messages.StringField(5)
    connection_id = messages.StringField(6)
    user_id = messages.StringField(7)
    user_name = messages.StringField(8)
    personthing_id = messages.StringField(9)
    personthing_name = messages.StringField(10)
    social_media_json = messages.StringField(11)
    created = message_types.DateTimeField(12)
    updated = message_types.DateTimeField(13)
    comment_id = messages.IntegerField(14)
    connection_title=messages.StringField(15)


class CommentsListResponse(messages.Message):
    """ProtoRPC message definition to represent a list of stored scores."""
    comments = messages.MessageField(CommentsResponseMessage, 1, repeated=True)
    cursor = messages.StringField(2)
    num_of_results = messages.IntegerField(3)


# CLASSES FOR ADDING COMMENTS
class CommentsAddRequest(messages.Message):
    """ProtoRPC message definition to represent a scores query."""
    title = messages.StringField(1)
    post_type =  messages.StringField(2)
    tags = messages.StringField(3)
    body = messages.StringField(4)
    media = messages.StringField(5)
    user_id = messages.StringField(6)
    personthing_id = messages.StringField(7)
    connection_id = messages.StringField(8)
    apikey = messages.IntegerField(9)

class CommentsAddResponse(messages.Message):
    """ProtoRPC message definition to represent a scores query."""
    message = messages.StringField(1)
    comment_id = messages.IntegerField(2)


# CLASSES FOR DELETE COMMENTS
class CommentsDeleteRequest(messages.Message):
    """ProtoRPC message definition to represent a scores query."""
    post_id = messages.StringField(1)

class CommentsDeleteResponse(messages.Message):
    """ProtoRPC message definition to represent a scores query."""
    message = messages.StringField(1)

# CLASSES FOR LOCATION
class HSLocationRequest(messages.Message):
    """ProtoRPC message definition to represent a scores query."""
    limit = messages.IntegerField(1)
    cursor = messages.StringField(2)
    type = messages.StringField(3)
    apikey = messages.IntegerField(4)

class LatLngMessage(messages.Message):
    """ProtoRPC message definition to represent a score that is stored."""
    title = messages.StringField(1)
    blog_url=messages.StringField(2)
    latitude = messages.FloatField(3)
    longitude = messages.FloatField(4)
    loc_name = messages.StringField(5)
    id = messages.IntegerField(6)
    created = message_types.DateTimeField(7)
    updated = message_types.DateTimeField(8)
    type = messages.StringField(9)

class HSLocationResponse(messages.Message):
    """ProtoRPC message definition to represent a list of stored scores."""
    locations = messages.MessageField(LatLngMessage, 1, repeated=True)
    cursor = messages.StringField(2)
    num_of_results = messages.IntegerField(3)

# CLASSES FOR LOCATION
class HSLocationAddRequest(messages.Message):
    """ProtoRPC message definition to represent a scores query."""
    title = messages.StringField(1)
    blog_url=messages.StringField(2)
    latitude = messages.FloatField(3)
    longitude = messages.FloatField(4)
    loc_name = messages.StringField(5)
    type = messages.StringField(6)
    apikey = messages.IntegerField(7)

class HSLocationAddResponse(messages.Message):
    """ProtoRPC message definition to represent a list of stored scores."""
    message = messages.StringField(1)
    new_connection_id = messages.IntegerField(2)


#Class for the login credential request
class LoginRequest(messages.Message):
    """ProtoRPC message definition to represent a url query."""
    username = messages.StringField(1)
    password = messages.StringField(2)

#Class for login response
class LoginResponse(messages.Message):
    """ProtoRPC message definition to represent a list of stored scores."""
    message = messages.StringField(1)
    status = messages.StringField(2)
    created = message_types.DateTimeField(3)
    updated = message_types.DateTimeField(4)
    id = messages.IntegerField(5)
    apikey = messages.IntegerField(6)


