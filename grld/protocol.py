import re
import select
import threading
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

infStr = "function() return math.huge end"
negInfStr = "function() return -math.huge end"
nanStr = "function() return 0/0 end"

def serialize( value ):
    t = type( value )
    if t == int or t == float:
        if value == float('inf'):
            res = infStr
        elif value == -float('inf'):
            res = negInfStr
        elif value == float('nan'):
            res = nanStr
        else:
            res = str( value )

        return res
    elif t == bool:
        return str(value).lower()
    elif t == str:
        return '"'+value.replace('"', '\\"')+'"'
    elif t == type(None):
        return "nil"
    elif t == dict:
        res = "{ "
        for k, v in value.items():
            res = res+"["+serialize( k )+"] = "+serialize( v )+", "
        res = res+" }"
        return res
    else:
        error( "Can't serialize a value of type "+str(t) )

def convert_lua_table_str_to_python_dict_str(s):
    subbed_s = re.sub(r"\[(.+?)\]\s*=\s*([\w\W]*?[,{])", r"\g<1>: \g<2>", s) # NOTE: does not support keys with newlines, also expects all keys to be wrapped in []
    return re.sub(r":\s*\"([\w\W]*?)\"([,{])", r': """\g<1>"""\g<2>', subbed_s) # replace '= "X"' with '= """X"""'


def deserialize( s ):
    ds = s.replace(infStr, "float('inf')")
    ds = ds.replace(negInfStr, "-float('inf')")
    ds = ds.replace(nanStr, "float('nan')")

    ds = ds.replace('true', 'True')
    ds = ds.replace('false', 'False')

    ds = ds.replace('nil', 'None')
    ds = ds.replace('\\\n\9', '\\\n')

    try:
        ds = convert_lua_table_str_to_python_dict_str(ds)
        result = eval(ds)
        return result
    except BaseException:
        e = sys.exc_info()[1]
        raise ProtocolException("Error deserializing message \n{}\n{}".format(s, e))

def assert_locked(func):
    def wrapper(self, *args, **kwargs):
        assert self.is_locked(), "Cannot access Protocol methods outside of a with statement! This is to ensure thread safety."
        return func(self, *args, **kwargs)

    return wrapper

class Protocol(object):
    """
    Class for connecting with debugger engine  ####which uses DBGp protocol.#### no longer true
    """

    # Maximum amount of data to be received at once by socket
    read_size = 1024

    def __init__(self, on_break_cmd_cb=None, on_synchronize_cmd_cb=None):
        # Set port number to listen for response
        self.port = get_value(S.KEY_PORT, S.DEFAULT_PORT)

        self.messages = [] # pulled from the lua client (a response to a message we sent)

        self.command_cbs = {}

        self.lock = threading.RLock()
        self.locked = 0
        self.listening_canceled_event = threading.Event()

        with self as s:
            s.clear()

    def __enter__(self):
        self.lock.acquire()
        self.locked += 1
        return self

    def __exit__(self, err_type, error_obj, traceback):
        self.lock.release()
        self.locked = max(self.locked - 1, 0)

    def is_locked(self):
        return self.locked > 0

    def register_command_cb(self, cmd_name, cb):
        cbs = self.command_cbs.setdefault(cmd_name, [])
        cbs.append(cb)

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

    @assert_locked
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

        #self.lock = threading.RLock()
        #self.locked = 0

        self.listening_canceled_event.clear()

    def stop_listening_for_incoming_connections(self):
        self.listening_canceled_event.set()

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

    @assert_locked
    def is_command(self, message):
        if not message:
            return False

        deserialized_message = deserialize(message)

        return deserialized_message in ('break', 'synchronize')

    @assert_locked
    def handle_command(self, message):
        command_name = deserialize(message)

        if command_name == 'break':
            filename = deserialize(self.read_next_message())
            line = deserialize(self.read_next_message())

            cbargs = (filename, line)

        elif command_name == 'synchronize':
            cbargs = tuple()

        cbs = self.command_cbs.get(command_name)
        if cbs and len(cbs) > 0:
            for cb in cbs:
                cb(*cbargs)


    @assert_locked
    def update(self):
        # read in messages (these might be commands which will be handled immediately)
        message = self.read_next_message(async=True)

        # if it's not a command, we need to keep it around for the next read request
        if message:
            self.messages.append(message)

    @assert_locked
    def parse_grld_message(self, message):
        """
        returns parsed_message, remaining_buffer_data
        """
        if len(message) == 0:
            return '', ''

        if message.count("\n") < 2:
            raise ProtocolException("Tried to parse malformed GRLD data")

        channel, messageSize, remaining = message.split("\n", 2)
        data = remaining[:int(messageSize)]
        remaining = remaining[int(messageSize):]

        return data, remaining


    @assert_locked
    def read_socket_into_buffer(self, async=False):
        """
        Get response data from debugger engine.
        """
        # Check socket connection
        if self.connected:
            # Get result data from debugger engine
            try:
                if async:
                    r, _, _ = select.select([self.socket], [], [], 0)
                    if not r:
                        return

                rawSockData = ''
                while True:
                    rawSockData = self.socket.recv(self.read_size)
                    self.buffer += H.data_read(rawSockData)

                    r, _, _ = select.select([self.socket], [], [], 0)
                    if not r:
                        break

            except:
                e = sys.exc_info()[1]
                raise ProtocolConnectionException(e)
        else:
            raise ProtocolConnectionException("GRLD is not connected")


    @assert_locked
    def read_next_message(self, async=False):
        """
        Update buffer from socket if buffer is empty.

        Parse out buffer data and return the next message.
        """
        # Verify length of response data
        # length = self.read_socket_into_buffer()

        if len(self.buffer) <= 0:
            self.read_socket_into_buffer(async)

        if len(self.buffer) <= 0:
            return None

        while True:
            message, self.buffer = self.parse_grld_message(self.buffer)

            if self.is_command(message):
                # kind of gross to do this here (heavy coupling, poor concern encapsulation), but it needs to happen immediately because the GRLD client might expect a response
                self.handle_command(message)
            else:
                break

        return message

    @assert_locked
    def read(self, return_string=False):
        if len(self.messages):
            message = self.messages.pop(0)
        else:
            message = self.read_next_message()

        if return_string:
            return message
        else:
            return deserialize(message)

    @assert_locked
    def send(self, data, channel='default'):
        self.update()
        s_data = serialize(data)
        formatted_data = channel + '\n' + str(len(s_data)) + '\n' + s_data

        self.socket.send(H.data_write(formatted_data))

    @assert_locked
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
            while not self.listening_canceled_event.is_set() and self.listening:
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