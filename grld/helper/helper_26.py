"""
Helper module for Python version 2.6 and below
- Ordered dictionaries
- Encoding/decoding urls
- Unicode
- Exception handling (except Exception, e)
"""

import base64
from urllib import unquote, quote
try:
	from ordereddict import OrderedDict
except:
	pass

def modulename():
	return "Helper module for Python version 2.6 and below"

def url_decode(uri):
	return unquote(uri)

def url_encode(uri):
	return quote(uri)

def new_dictionary():
	try:
		return OrderedDict()
	except:
		return {}

def dictionary_keys(dictionary):
	return dictionary.keys()

def dictionary_values(dictionary):
	return dictionary.values()

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

def unicode_chr(code):
	return unichr(code)

def unicode_string(string):
	if isinstance(string, unicode):
		return string
	return string.decode('utf8', 'replace')

def is_digit(string):
	# Check if basestring (str, unicode) is digit
	return isinstance(string, basestring) and string.isdigit()

def is_number(value):
	return isinstance(value, (int, long))