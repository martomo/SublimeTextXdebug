import re
import socket
import sys

# Helper module
try:
    from .helper import H
except:
    from helper import H

# Settings variables
try:
    from . import settings as S
except:
    import settings as S

# Config module
from .config import get_value

# Log module
from .log import debug

# HTML entities
try:
    from html.entities import name2codepoint
except ImportError:
    from htmlentitydefs import name2codepoint

# XML parser
try:
    from xml.etree import cElementTree as ET
except ImportError:
    try:
        from xml.etree import ElementTree as ET
    except ImportError:
        from .elementtree import ElementTree as ET
try:
    from xml.parsers import expat
    UNESCAPE_RESPONSE_DATA = True
except ImportError:
    # Module xml.parsers.expat missing, using SimpleXMLTreeBuilder
    from .elementtree import SimpleXMLTreeBuilder
    ET.XMLTreeBuilder = SimpleXMLTreeBuilder.TreeBuilder
    UNESCAPE_RESPONSE_DATA = False


ILLEGAL_XML_UNICODE_CHARACTERS = [
    (0x00, 0x08), (0x0B, 0x0C), (0x0E, 0x1F), (0x7F, 0x84),
    (0x86, 0x9F), (0xD800, 0xDFFF), (0xFDD0, 0xFDDF),
    (0xFFFE, 0xFFFF),
    (0x1FFFE, 0x1FFFF), (0x2FFFE, 0x2FFFF), (0x3FFFE, 0x3FFFF),
    (0x4FFFE, 0x4FFFF), (0x5FFFE, 0x5FFFF), (0x6FFFE, 0x6FFFF),
    (0x7FFFE, 0x7FFFF), (0x8FFFE, 0x8FFFF), (0x9FFFE, 0x9FFFF),
    (0xAFFFE, 0xAFFFF), (0xBFFFE, 0xBFFFF), (0xCFFFE, 0xCFFFF),
    (0xDFFFE, 0xDFFFF), (0xEFFFE, 0xEFFFF), (0xFFFFE, 0xFFFFF),
    (0x10FFFE, 0x10FFFF) ]

ILLEGAL_XML_RANGES = ["%s-%s" % (H.unicode_chr(low), H.unicode_chr(high))
                  for (low, high) in ILLEGAL_XML_UNICODE_CHARACTERS
                  if low < sys.maxunicode]

ILLEGAL_XML_RE = re.compile(H.unicode_string('[%s]') % H.unicode_string('').join(ILLEGAL_XML_RANGES))



class Protocol(object):
    """
    Class for connecting with debugger engine which uses DBGp protocol.
    """

    # Maximum amount of data to be received at once by socket
    read_size = 1024

    def __init__(self):
        # Set port number to listen for response
        self.port = get_value(S.KEY_PORT, S.DEFAULT_PORT)
        self.clear()

    def transaction_id():
        """
        Standard argument for sending commands, an unique numerical ID.
        """
        def fget(self):
            self._transaction_id += 1
            return self._transaction_id

        def fset(self, value):
            self._transaction_id = value

        def fdel(self):
            self._transaction_id = 0
        return locals()

    # Transaction ID property
    transaction_id = property(**transaction_id())

    def clear(self):
        """
        Clear variables, reset transaction_id, close socket connection.
        """
        self.buffer = ''
        self.connected = False
        self.listening = False
        del self.transaction_id
        try:
            self.socket.close()
        except:
            pass
        self.socket = None

    def unescape(self, string):
        """
        Convert HTML entities and character references to ordinary characters.
        """
        def convert(matches):
            text = matches.group(0)
            # Character reference
            if text[:2] == "&#":
                try:
                    if text[:3] == "&#x":
                        return H.unicode_chr(int(text[3:-1], 16))
                    else:
                        return H.unicode_chr(int(text[2:-1]))
                except ValueError:
                    pass
            # Named entity
            else:
                try:
                    # Following are not needed to be converted for XML
                    if text[1:-1] == "amp" or text[1:-1] == "gt" or text[1:-1] == "lt":
                        pass
                    else:
                        text = H.unicode_chr(name2codepoint[text[1:-1]])
                except KeyError:
                    pass
            return text
        return re.sub("&#?\w+;", convert, string)

    def read_until_null(self):
        """
        Get response data from debugger engine.
        """
        # Check socket connection
        if self.connected:
            # Get result data from debugger engine
            try:
                while not '\x00' in self.buffer:
                    self.buffer += H.data_read(self.socket.recv(self.read_size))
                data, self.buffer = self.buffer.split('\x00', 1)
                return data
            except:
                e = sys.exc_info()[1]
                raise ProtocolConnectionException(e)
        else:
            raise ProtocolConnectionException("Xdebug is not connected")

    def read_data(self):
        """
        Get response data from debugger engine and verify length of response.
        """
        # Verify length of response data
        length = self.read_until_null()
        message = self.read_until_null()
        if int(length) == len(message):
            return message
        else:
            raise ProtocolException("Length mismatch encountered while reading the Xdebug message")

    def read(self, return_string=False):
        """
        Get response from debugger engine as XML document object.
        """
        # Get result data from debugger engine and verify length of response
        data = self.read_data()

        # Show debug output
        debug('[Response data] %s' % data)

        # Return data string
        if return_string:
            return data

        # Remove special character quoting
        if UNESCAPE_RESPONSE_DATA:
            data = self.unescape(data)

        # Replace invalid XML characters
        data = ILLEGAL_XML_RE.sub('?', data)

        # Create XML document object
        document = ET.fromstring(data)
        return document

    def send(self, command, *args, **kwargs):
        """
        Send command to the debugger engine according to DBGp protocol.
        """
        # Expression is used for conditional and watch type breakpoints
        expression = None

        # Seperate 'expression' from kwargs
        if 'expression' in kwargs:
            expression = kwargs['expression']
            del kwargs['expression']

        # Generate unique Transaction ID
        transaction_id = self.transaction_id

        # Append command/arguments to build list
        build_command = [command, '-i %i' % transaction_id]
        if args:
            build_command.extend(args)
        if kwargs:
            build_command.extend(['-%s %s' % pair for pair in kwargs.items()])

        # Remove leading/trailing spaces and build command string
        build_command = [part.strip() for part in build_command if part.strip()]
        command = ' '.join(build_command)
        if expression:
            command += ' -- ' + H.base64_encode(expression)

        # Show debug output
        debug('[Send command] %s' % command)

        # Send command to debugger engine
        try:
            self.socket.send(H.data_write(command + '\x00'))
        except:
            e = sys.exc_info()[1]
            raise ProtocolConnectionException(e)

    def listen(self):
        """
        Create socket server which listens for connection on configured port.
        """
        # Create socket server
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if server:
            # Configure socket server
            try:
                server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server.settimeout(1)
                server.bind(('', self.port))
                server.listen(1)
                self.listening = True
                self.socket = None
            except:
                e = sys.exc_info()[1]
                raise ProtocolConnectionException(e)

            # Accept incoming connection on configured port
            while self.listening:
                try:
                    self.socket, address = server.accept()
                    self.listening = False
                except socket.timeout:
                    pass

            # Check if a connection has been made
            if self.socket:
                self.connected = True
                self.socket.settimeout(None)
            else:
                self.connected = False
                self.listening = False

            # Close socket server
            try:
                server.close()
            except:
                pass
            server = None

            # Return socket connection
            return self.socket
        else:
            raise ProtocolConnectionException('Could not create socket server.')


class ProtocolException(Exception):
    pass


class ProtocolConnectionException(ProtocolException):
    pass