"""
Status and feature management commands
"""
STATUS = 'status'
FEATURE_GET = 'feature_get'
FEATURE_SET = 'feature_set'

"""
Feature names
"""
FEATURE_NAME_BREAKPOINT_LANGUAGES = 'breakpoint_languages'
FEATURE_NAME_BREAKPOINT_TYPES = 'breakpoint_types'
FEATURE_NAME_DATA_ENCODING = 'data_encoding'
FEATURE_NAME_ENCODING = 'encoding'
FEATURE_NAME_EXTENDED_PROPERTIES = 'extended_properties'
FEATURE_NAME_LANGUAGE_NAME = 'language_name'
FEATURE_NAME_LANGUAGE_SUPPORTS_THREADS = 'language_supports_threads'
FEATURE_NAME_LANGUAGE_VERSION = 'language_version'
FEATURE_NAME_MAX_CHILDREN = 'max_children'
FEATURE_NAME_MAX_DATA = 'max_data'
FEATURE_NAME_MAX_DEPTH = 'max_depth'
FEATURE_NAME_MULTIPLE_SESSIONS = 'multiple_sessions'
FEATURE_NAME_NOTIFY_OK = 'notify_ok'
FEATURE_NAME_PROTOCOL_VERSION = 'protocol_version'
FEATURE_NAME_RESOLVED_BREAKPOINTS = 'resolved_breakpoints'
FEATURE_NAME_SHOW_HIDDEN = 'show_hidden'
FEATURE_NAME_SUPPORTED_ENCODINGS = 'supported_encodings'
FEATURE_NAME_SUPPORTS_ASYNC = 'supports_async'
FEATURE_NAME_SUPPORTS_POSTMORTEM = 'supports_postmortem'

"""
Continuation commands
"""
RUN = 'run'
STEP_INTO = 'step_into'
STEP_OVER = 'step_over'
STEP_OUT = 'step_out'
STOP = 'stop'
DETACH = 'detach'

"""
Breakpoint commands
"""
BREAKPOINT_SET = 'breakpoint_set'
BREAKPOINT_GET = 'breakpoint_get'
BREAKPOINT_UPDATE = 'breakpoint_update'
BREAKPOINT_REMOVE = 'breakpoint_remove'
BREAKPOINT_LIST = 'breakpoint_list'

"""
Context/Stack/Property commands
"""
CONTEXT_NAMES = 'context_names'
CONTEXT_GET = 'context_get'
STACK_DEPTH = 'stack_depth'
STACK_GET = 'stack_get'
PROPERTY_GET = 'property_get'
PROPERTY_SET = 'property_set'
PROPERTY_VALUE = 'property_value'

"""
Context ids
"""
CONTEXT_ID_LOCALS = 0
CONTEXT_ID_SUPERGLOBALS = 1
CONTEXT_ID_USER_DEFINED = 2

"""
Extended commands
"""
SOURCE = 'source'
STDERR = 'stderr'
STDOUT = 'stdout'
STDIN = 'stdin'
BREAK = 'break'
EVAL = 'eval'
EXPR = 'expr'
EXEC = 'exec'

"""
Status codes
"""
STATUS_STARTING = 'starting'
STATUS_STOPPING = 'stopping'
STATUS_STOPPED = 'stopped'
STATUS_RUNNING = 'running'
STATUS_BREAK = 'break'

"""
Reason codes
"""
REASON_OK = 'ok'
REASON_ERROR = 'error'
REASON_ABORTED = 'aborted'
REASON_EXCEPTION = 'exception'

"""
Response attributes/elements
"""
ATTRIBUTE_STATUS = 'status'
ATTRIBUTE_REASON = 'reason'
ATTRIBUTE_SUCCESS = 'success'
ATTRIBUTE_BREAKPOINT_ID = 'id'
ATTRIBUTE_BREAKPOINT_STATE = 'state'
ATTRIBUTE_BREAKPOINT_RESOLVED = 'resolved'
ATTRIBUTE_CONTEXT_ID = 'context'
ATTRIBUTE_FEATURE = 'feature'
ATTRIBUTE_FEATURE_NAME = 'feature_name'
ATTRIBUTE_FEATURE_SUPPORTED = 'supported'
ATTRIBUTE_STACK_DEPTH = 'depth'

ELEMENT_BREAKPOINT = 'xdebug:message'
ELEMENT_CONTEXT = 'context'
ELEMENT_ERROR = 'error'
ELEMENT_MESSAGE = 'message'
ELEMENT_PROPERTY = 'property'
ELEMENT_STACK = 'stack'

ELEMENT_PATH_BREAKPOINT = '{https://xdebug.org/dbgp/xdebug}message'
ELEMENT_PATH_ERROR = '{urn:debugger_protocol_v1}error'
ELEMENT_PATH_MESSAGE = '{urn:debugger_protocol_v1}message'
ELEMENT_PATH_PROPERTY = '{urn:debugger_protocol_v1}property'
ELEMENT_PATH_STACK = '{urn:debugger_protocol_v1}stack'

"""
Notify attributes/elements
"""
NOTIFY_NAME = 'name'
NOTIFY_ENCODING = 'encoding'

NOTIFY_ELEMENT_MESSAGE = 'xdebug:message'
NOTIFY_ELEMENT_PATH_MESSAGE = '{https://xdebug.org/dbgp/xdebug}message'

NOTIFY_MESSAGE_FILENAME = 'filename'
NOTIFY_MESSAGE_LINENO = 'lineno'
NOTIFY_MESSAGE_TYPE_STRING = 'type_string'

"""
Initialization attributes
"""
INIT_APPID = 'appid'
INIT_IDEKEY = 'idekey'
INIT_SESSION = 'session'
INIT_THREAD = 'thread'
INIT_PARENT = 'parent'
INIT_LANGUAGE = 'language'
INIT_LANGUAGE_VERSION = 'xdebug:language_version'
INIT_PROTOCOL_VERSION = 'protocol_version'
INIT_FILEURI = 'fileuri'

"""
Breakpoint attributes
"""
BREAKPOINT_TYPE = 'type'
BREAKPOINT_FILENAME = 'filename'
BREAKPOINT_LINENO = 'lineno'
BREAKPOINT_STATE = 'state'
BREAKPOINT_FUNCTION = 'function'
BREAKPOINT_CLASS = 'class'
BREAKPOINT_TEMPORARY = 'temporary'
BREAKPOINT_RESOLVED = 'resolved'
BREAKPOINT_HIT_COUNT = 'hit_count'
BREAKPOINT_HIT_VALUE = 'hit_value'
BREAKPOINT_HIT_CONDITION = 'hit_condition'
BREAKPOINT_EXCEPTION = 'exception'
BREAKPOINT_CODE = 'code'
BREAKPOINT_EXPRESSION = 'expression'

BREAKPOINT_STATE_TEMPORARY = 'temporary'
BREAKPOINT_STATE_DISABLED = 'disabled'
BREAKPOINT_STATE_ENABLED = 'enabled'

"""
Context attributes
"""
CONTEXT_ID = 'id'
CONTEXT_NAME = 'name'

"""
Error attributes
"""
ERROR_CODE = 'code'
ERROR_EXCEPTION = 'exception'

"""
Property attributes/elements
"""
PROPERTY_NAME = 'name'
PROPERTY_FULLNAME = 'fullname'
PROPERTY_CLASSNAME = 'classname'
PROPERTY_PAGE = 'page'
PROPERTY_PAGESIZE = 'pagesize'
PROPERTY_TYPE = 'type'
PROPERTY_FACET = 'facet'
PROPERTY_SIZE = 'size'
PROPERTY_CHILDREN = 'children'
PROPERTY_NUMCHILDREN = 'numchildren'
PROPERTY_KEY = 'key'
PROPERTY_ADDRESS = 'address'
PROPERTY_ENCODING = 'encoding'

PROPERTY_ELEMENT_NAME = 'name'
PROPERTY_ELEMENT_FULLNAME = 'fullname'
PROPERTY_ELEMENT_CLASSNAME = 'classname'
PROPERTY_ELEMENT_VALUE = 'value'

"""
Stack attributes
"""
STACK_LEVEL = 'level'
STACK_TYPE = 'type'
STACK_FILENAME = 'filename'
STACK_LINENO = 'lineno'
STACK_WHERE = 'where'
STACK_CMDBEGIN = 'cmdbegin'
STACK_CMDEND = 'cmdend'
