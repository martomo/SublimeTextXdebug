"""
Helper module for Python version 2.7
- Ordered dictionaries
- Encoding/decoding urls
- Unicode
- Exception handling (except Exception as e)
"""

import base64
import collections
import urllib.parse

def modulename():
	return "Helper module for Python version 2.7"

def url_decode(uri):
	return urllib.parse.unquote(uri)

def url_encode(uri):
	return urllib.parse.quote(uri)

def new_dictionary():
	return collections.OrderedDict()

def dictionary_keys(dictionary):
	return list(dictionary.keys())

def dictionary_values(dictionary):
	return list(dictionary.values())

def data_read(data):
	# Data for reading/receiving already a string in version 2.*
	return data

def data_write(data):
	# Using string in version 2.* for sending/writing data
	return data

def base64_decode(data):
	return base64.b64decode(data)

def base64_encode(data):
	return base64.b64encode(data)

def unicode_string(string):
	return unicode(string)

def is_digit(string):
	# Check if basestring (str, unicode) is digit
	return isinstance(string, basestring) and string.isdigit()