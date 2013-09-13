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

# Log module
from .log import debug

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
except ImportError:
    # Module xml.parsers.expat missing, using SimpleXMLTreeBuilder
    from .elementtree import SimpleXMLTreeBuilder
    ET.XMLTreeBuilder = SimpleXMLTreeBuilder.TreeBuilder


class Protocol(object):
    """
    Class for connecting with debugger engine which uses DBGp protocol.
    """

    # Maximum amount of data to be received at once by socket
    read_size = 1024

    def __init__(self):
        # Set port number to listen for response
        self.port = S.get_config_value('port', S.DEFAULT_PORT)
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