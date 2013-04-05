import sublime

import socket
import sys
from xml.dom.minidom import parseString

# Helper class
try:
    from .helper import H
except:
    from helper import H

# Global variables
try:
    from . import settings as S
except:
    import settings as S

# DBGp protocol constants
try:
    from . import dbgp
except:
    import dbgp


class Protocol(object):
    """
    Class for connecting with debugger engine which uses DBGp protocol.
    """

    # Maximum amount of data to be received at once by socket
    read_size = 1024

    def __init__(self):
        # Set port number to listen for response
        self.port = S.get_project_value('port') or S.get_package_value('port') or S.DEFAULT_PORT
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
            while not '\x00' in self.buffer:
                self.buffer += H.socket_recv(self.socket.recv(self.read_size))
            data, self.buffer = self.buffer.split('\x00', 1)
            return data
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

    def read(self):
        """
        Get response from debugger engine as XML document object.
        """
        # Get result data from debugger engine and verify length of response
        data = self.read_data()
        # Show debug output
        if S.DEBUG: print('[Response data] ', data)
        # Create XML document object
        document = parseString(data)
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

        # Send command to debugger engine
        try:
            self.socket.send(H.socket_send(command + '\x00'))
            # Show debug output
            if S.DEBUG: print('[Send command] ', command)
        except:
            e = sys.exc_info()[1]
            raise ProtocolConnectionException(e)

    def listen(self):
        """
        Create socket server which listens for connection on configured port
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
                server = None
            except:
                pass

            # Return socket connection
            return self.socket
        else:
            raise ProtocolConnectionException('Could not create socket server.')


class DebuggerException(Exception):
    pass


class ProtocolException(DebuggerException):
    pass


class ProtocolConnectionException(ProtocolException):
    pass


def is_connected():
    if S.SESSION and S.SESSION.connected:
        return True
    elif S.SESSION:
        sublime.status_message('Xdebug: Waiting response from debugger engine.')
    else:
        sublime.status_message('Xdebug: No Xdebug session running.')
    return False


def get_context_values(node):
    values = H.unicode_string('')
    for child in node.childNodes:
        # Get property attribute values
        if child.nodeName == dbgp.ELEMENT_PROPERTY:
            property_name = H.unicode_string(child.getAttribute(dbgp.PROPERTY_FULLNAME))
            property_type = H.unicode_string(child.getAttribute(dbgp.PROPERTY_TYPE))
            property_value = None
            try:
                # Try to base64 decode value
                property_value = H.unicode_string(' '.join(H.base64_decode(t.data) for t in child.childNodes if t.nodeType == t.TEXT_NODE or t.nodeType == t.CDATA_SECTION_NODE))
            except:
                # Return raw value
                property_value = H.unicode_string(' '.join(t.data for t in child.childNodes if t.nodeType == t.TEXT_NODE or t.nodeType == t.CDATA_SECTION_NODE))
            if property_name:
                # Hide password values
                if property_name.lower().find('password') != -1:
                    property_value = H.unicode_string('*****')

                # Append values and get values for child
                values = values + H.unicode_string(property_name + ' [' + property_type + '] = ' + property_value + '\n')
                values = values + get_context_values(child)
    return values


def get_stack_values(node):
    values = H.unicode_string('')
    for child in node.childNodes:
        # Get stack attribute values
        if child.nodeName == dbgp.ELEMENT_STACK:
            stack_level = child.getAttribute(dbgp.STACK_LEVEL)
            stack_type = child.getAttribute(dbgp.STACK_TYPE)
            stack_file = H.url_decode(child.getAttribute(dbgp.STACK_FILENAME))
            stack_line = child.getAttribute(dbgp.STACK_LINENO)
            stack_where = child.getAttribute(dbgp.STACK_WHERE)
            # Append values
            values = values + H.unicode_string('{level:>3}: {type:<10} {where:<10} {filename}:{lineno}\n' \
                                      .format(level=stack_level, type=stack_type, where=stack_where, lineno=stack_line, filename=stack_file))
    return values