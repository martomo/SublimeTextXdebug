import sublime

import socket
import sys
from xml.dom.minidom import parseString

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

# DBGp protocol constants
try:
    from . import dbgp
except:
    import dbgp

from .log import debug


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
                self.buffer += H.data_read(self.socket.recv(self.read_size))
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
        debug('[Response data] %s' % data)
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
            self.socket.send(H.data_write(command + '\x00'))
            # Show debug output
            debug('[Send command] %s' % command)
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


def connection_error(message):
    sublime.error_message("Please restart Xdebug debugging session.\nDisconnected from Xdebug debugger engine.\n"+message)
    # Reset connection
    try:
        S.SESSION.clear()
    except:
        pass
    finally:
        S.SESSION = None
        S.BREAKPOINT_ROW = None
        S.CONTEXT_DATA.clear()


def get_breakpoint_values():
    # Get breakpoints for files
    values = H.unicode_string('')
    if S.BREAKPOINT is None:
        return values
    for filename, breakpoint_data in sorted(S.BREAKPOINT.items()):
        breakpoint_entry = ''
        if breakpoint_data:
            breakpoint_entry += "=> %s\n" % filename
            # Sort breakpoint data by line number
            for lineno, bp in sorted(breakpoint_data.items(), key=lambda item: (int(item[0]) if isinstance(item[0], int) or H.is_digit(item[0]) else float('inf'), item[0])):
                breakpoint_entry += '\t'
                if bp['enabled']:
                    breakpoint_entry += '|+|'
                else:
                    breakpoint_entry += '|-|'
                breakpoint_entry += ' %s' % lineno
                if bp['expression'] is not None:
                    breakpoint_entry += ' -- "%s"' % bp['expression']
                breakpoint_entry += "\n"
        values += H.unicode_string(breakpoint_entry)
    return values


def get_context_values():
    """
    #TODO: Get all variables by looping context_names
    """
    if S.SESSION:
        try:
            # Only show first level variables
            S.SESSION.send(dbgp.FEATURE_SET, n=dbgp.FEATURE_NAME_MAXCHILDREN, v='0')
            response = S.SESSION.read().firstChild

            # Local variables
            S.SESSION.send(dbgp.CONTEXT_GET)
            response = S.SESSION.read().firstChild

            # Retrieve properties from response
            context = get_response_properties(response)

            # Store context variables in session
            S.CONTEXT_DATA = context

            return generate_context_output(context)
        except (socket.error, ProtocolConnectionException):
            e = sys.exc_info()[1]
            connection_error("%s" % e)


def get_context_variable(context, variable_name):
    """
    Find a variable in the context data
    """
    if isinstance(context, dict):
        if variable_name in context:
            return context[variable_name]
        for variable in context.values():
            if isinstance(variable['children'], dict):
                children = get_context_variable(variable['children'], variable_name)
                if children:
                    return children


def get_property_children(property_name, numchildren):
    if S.SESSION:
        # Set max children limit accordingly
        S.SESSION.send(dbgp.FEATURE_SET, n=dbgp.FEATURE_NAME_MAXCHILDREN, v=numchildren)
        response = S.SESSION.read().firstChild

        # Get property and it's children
        S.SESSION.send(dbgp.PROPERTY_GET, n=property_name)
        response = S.SESSION.read().firstChild

        # Walk through elements in response
        for child in response.childNodes:
            # Only read property elements
            if child.nodeName == dbgp.ELEMENT_PROPERTY:
                # Return it's children when property matches property name
                if property_name == H.unicode_string(child.getAttribute(dbgp.PROPERTY_FULLNAME)):
                    return get_response_properties(child)
    return {}


def get_response_properties(response):
    properties = H.new_dictionary()
    # Walk through elements in response
    for child in response.childNodes:
        # Only read property elements
        if child.nodeName == dbgp.ELEMENT_PROPERTY:
            # Get property attribute values
            property_name = H.unicode_string(child.getAttribute(dbgp.PROPERTY_FULLNAME))
            property_type = H.unicode_string(child.getAttribute(dbgp.PROPERTY_TYPE))
            property_children = H.unicode_string(child.getAttribute(dbgp.PROPERTY_CHILDREN))
            property_numchildren = H.unicode_string(child.getAttribute(dbgp.PROPERTY_NUMCHILDREN))
            property_classname = H.unicode_string(child.getAttribute(dbgp.PROPERTY_CLASSNAME))
            property_value = None

            # Ignore following properties
            if property_name == "::":
                continue
            # Avoid nasty static functions/variables from turning in an infinitive loop
            if property_name.count("::") > 1:
                continue

            try:
                # Try to base64 decode value
                property_value = H.unicode_string(' '.join(H.base64_decode(t.data) for t in child.childNodes if t.nodeType == t.TEXT_NODE or t.nodeType == t.CDATA_SECTION_NODE))
            except:
                # Return raw value
                property_value = H.unicode_string(' '.join(t.data for t in child.childNodes if t.nodeType == t.TEXT_NODE or t.nodeType == t.CDATA_SECTION_NODE))
            if property_name:
                # Filter password values
                if property_name.lower().find('password') != -1:
                    property_value = H.unicode_string('*****')

                # Store property
                properties[property_name] = { 'name': property_name, 'type': property_type, 'value': property_value, 'children' : None }

                # Get values for children
                if property_children:
                    properties[property_name]['children'] = get_property_children(property_name, property_numchildren)

                # Set classname, if available, as type for object
                if property_classname and property_type == 'object':
                    properties[property_name]['type'] = property_classname
    return properties


def get_stack_values():
    values = H.unicode_string('')
    if S.SESSION:
        try:
            # Get stack information
            S.SESSION.send(dbgp.STACK_GET)
            response = S.SESSION.read().firstChild

            for child in response.childNodes:
                # Get stack attribute values
                if child.nodeName == dbgp.ELEMENT_STACK:
                    stack_level = child.getAttribute(dbgp.STACK_LEVEL)
                    stack_type = child.getAttribute(dbgp.STACK_TYPE)
                    stack_file = H.url_decode(child.getAttribute(dbgp.STACK_FILENAME))
                    stack_line = child.getAttribute(dbgp.STACK_LINENO)
                    stack_where = child.getAttribute(dbgp.STACK_WHERE)
                    # Append values
                    values += H.unicode_string('[{level}] {filename}.{where}:{lineno}\n' \
                                              .format(level=stack_level, type=stack_type, where=stack_where, lineno=stack_line, filename=stack_file))
        except (socket.error, ProtocolConnectionException):
            e = sys.exc_info()[1]
            connection_error("%s" % e)
    return values


def generate_context_output(context, indent=0):
    # Generate output text for values
    values = H.unicode_string('')
    if not isinstance(context, dict):
        return values
    for variable in context.values():
        property_text = ''
        for i in range(indent): property_text += '\t'
        if variable['value']:
            # Remove newlines in value to prevent incorrect indentation
            value = variable['value'].replace("\r\n", "\n").replace("\n", " ")
            property_text += variable['name'] + ' = (' + variable['type'] + ') ' + value + '\n'
        elif isinstance(variable['children'], dict):
            property_text += variable['name'] + ' = ' + variable['type'] + '[%d]\n' % len(variable['children'])
            property_text += generate_context_output(variable['children'], indent+1)
        else:
            property_text += variable['name'] + ' = <' + variable['type'] + '>\n'
        values += H.unicode_string(property_text)
    return values