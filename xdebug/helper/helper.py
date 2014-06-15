"""
Helper module for Python version 3.0 and above
- Ordered dictionaries
- Encoding/decoding urls
- Unicode/Bytes (for sending/receiving data from/to socket, base64)
- Exception handling (except Exception as e)
"""

import base64
import urllib.parse
from collections import OrderedDict

def modulename():
	return "Helper module for Python version 3.0 and above"

def url_decode(uri):
	return urllib.parse.unquote(uri)

def url_encode(uri):
	return urllib.parse.quote(uri)

def new_dictionary():
	return OrderedDict()

def dictionary_keys(dictionary):
	return list(dictionary.keys())

def dictionary_values(dictionary):
	return list(dictionary.values())

def data_read(data):
	# Convert bytes to string
	return data.decode('utf8')

def data_write(data):
	# Convert string to bytes
	return bytes(data, 'utf8')

def base64_decode(data):
	# Base64 returns decoded byte string, decode to convert to UTF8 string
	return base64.b64decode(data).decode('utf8')

def base64_encode(data):
	# Base64 needs ascii input to encode, which returns Base64 byte string, decode to convert to UTF8 string
	return base64.b64encode(data.encode('ascii')).decode('utf8')

def unicode_chr(code):
	return chr(code)

def unicode_string(string):
	# Python 3.* uses unicode by default
	return string

def is_digit(string):
	# Check if string is digit
	return isinstance(string, str) and string.isdigit()

def is_number(value):
	return isinstance(value, int)