import sublime

import sys
import threading

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

# Log module
from .log import debug, info

# Protocol module
from .protocol import ProtocolConnectionException

# Util module
from .util import get_real_path

# View module
from .view import DATA_CONTEXT, DATA_STACK, DATA_WATCH, generate_context_output, generate_stack_output, get_response_properties, render_regions, show_content, show_file, show_panel_content


ACTION_EVALUATE = "action_evaluate"
ACTION_EXECUTE = "action_execute"
ACTION_INIT = "action_init"
ACTION_REMOVE_BREAKPOINT = "action_remove_breakpoint"
ACTION_SET_BREAKPOINT = "action_set_breakpoint"
ACTION_STATUS = "action_status"
ACTION_USER_EXECUTE = "action_user_execute"
ACTION_WATCH = "action_watch"


def is_connected(show_status=False):
    """
    Check if client is connected to debugger engine.

    Keyword arguments:
    show_status -- Show message why client is not connected in status bar.
    """
    if S.SESSION and S.SESSION.connected:
        return True
    elif S.SESSION and show_status:
        sublime.status_message('Xdebug: Waiting for response from debugger engine.')
    elif show_status:
        sublime.status_message('Xdebug: No Xdebug session running.')
    return False


def connection_error(message):
    """
    Template for showing error message on connection error/loss.

    Keyword arguments:
    message -- Exception/reason of connection error/loss.
    """
    sublime.error_message("Please restart Xdebug debugging session.\nDisconnected from Xdebug debugger engine.\n" + message)
    info("Connection lost with debugger engine.")
    debug(message)
    # Reset connection
    try:
        S.SESSION.clear()
    except:
        pass
    finally:
        S.SESSION = None
        S.SESSION_BUSY = False
        S.BREAKPOINT_ROW = None
        S.BREAKPOINT_RUN = None
        S.CONTEXT_DATA.clear()
        async_session = SocketHandler(ACTION_WATCH)
        async_session.start()
    # Reset layout
    sublime.active_window().run_command('xdebug_layout')
    # Render breakpoint markers
    render_regions()


class SocketHandler(threading.Thread):
    def __init__(self, action, **options):
        threading.Thread.__init__(self)
        self.action = action
        self.options = options

    def get_option(self, option, default_value=None):
        if option in self.options.keys():
            return self.options[option]
        return default_value

    def run_command(self, command, args=None):
        if not isinstance(args, dict):
            args = {}
        self.timeout(lambda: sublime.active_window().run_command(command, args))

    def run_view_command(self, command, args=None):
        if not isinstance(args, dict):
            args = {}
        self.timeout(lambda: sublime.active_window().active_view().run_command(command, args))

    def status_message(self, message):
        self.timeout(lambda: sublime.status_message(message))

    def timeout(self, function):
        sublime.set_timeout(function, 0)

    def run(self):
        # Make sure an action is defined
        if not self.action:
            return
        try:
            S.SESSION_BUSY = True
            # Evaluate
            if self.action == ACTION_EVALUATE:
                self.evaluate(self.get_option('expression'))
            # Execute
            elif self.action == ACTION_EXECUTE:
                self.execute(self.get_option('command'))
            # Init
            elif self.action == ACTION_INIT:
                self.init()
            # Remove breakpoint
            elif self.action == ACTION_REMOVE_BREAKPOINT:
                self.remove_breakpoint(self.get_option('breakpoint_id'))
            # Set breakpoint
            elif self.action == ACTION_SET_BREAKPOINT:
                self.set_breakpoint(self.get_option('filename'), self.get_option('lineno'), self.get_option('expression'))
            # Status
            elif self.action == ACTION_STATUS:
                self.status()
            # User defined execute
            elif self.action == ACTION_USER_EXECUTE:
                self.user_execute(self.get_option('command'), self.get_option('args'))
            # Watch expression
            elif self.action == ACTION_WATCH:
                self.watch_expression()
        # Show dialog on connection error
        except ProtocolConnectionException:
            e = sys.exc_info()[1]
            self.timeout(lambda: connection_error("%s" % e))
        finally:
            S.SESSION_BUSY = False


    def evaluate(self, expression):
        if not expression or not is_connected():
            return
        # Send 'eval' command to debugger engine with code to evaluate
        S.SESSION.send(dbgp.EVAL, expression=expression)
        if self.get_option('pretty_output'):
            response = S.SESSION.read()
            properties = get_response_properties(response, expression)
            response = generate_context_output(properties)
        else:
            response = S.SESSION.read(return_string=True)

        # Show response data in output panel
        self.timeout(lambda: show_panel_content(response))


    def execute(self, command):
        # Do not execute if no command is set
        if not command or not is_connected():
            return

        # Send command to debugger engine
        S.SESSION.send(command)
        response = S.SESSION.read()

        # Reset previous breakpoint values
        S.BREAKPOINT_ROW = None
        S.CONTEXT_DATA.clear()
        self.watch_expression()
        # Set debug layout
        self.run_command('xdebug_layout')

        # Handle breakpoint hit
        for child in response:
            if child.tag == dbgp.ELEMENT_BREAKPOINT or child.tag == dbgp.ELEMENT_PATH_BREAKPOINT:
                # Get breakpoint attribute values
                fileuri = child.get(dbgp.BREAKPOINT_FILENAME)
                lineno = child.get(dbgp.BREAKPOINT_LINENO)
                filename = get_real_path(fileuri)
                # Check if temporary breakpoint is set and hit
                if S.BREAKPOINT_RUN is not None and S.BREAKPOINT_RUN['filename'] == filename and S.BREAKPOINT_RUN['lineno'] == lineno:
                    # Remove temporary breakpoint
                    if S.BREAKPOINT_RUN['filename'] in S.BREAKPOINT and S.BREAKPOINT_RUN['lineno'] in S.BREAKPOINT[S.BREAKPOINT_RUN['filename']]:
                        self.run_view_command('xdebug_breakpoint', {'rows': [S.BREAKPOINT_RUN['lineno']], 'filename': S.BREAKPOINT_RUN['filename']})
                    S.BREAKPOINT_RUN = None
                # Skip if temporary breakpoint was not hit
                if S.BREAKPOINT_RUN is not None and (S.BREAKPOINT_RUN['filename'] != filename or S.BREAKPOINT_RUN['lineno'] != lineno):
                    self.run_command('xdebug_execute', {'command': 'run'})
                    return
                # Show debug/status output
                self.status_message('Xdebug: Breakpoint')
                info('Break: ' + filename + ':' + lineno)
                # Store line number of breakpoint for displaying region marker
                S.BREAKPOINT_ROW = { 'filename': filename, 'lineno': lineno }
                # Focus/Open file window view
                self.timeout(lambda: show_file(filename, lineno))

        # On breakpoint get context variables and stack history
        if response.get(dbgp.ATTRIBUTE_STATUS) == dbgp.STATUS_BREAK:
            # Context variables
            context = self.get_context_values()
            self.timeout(lambda: show_content(DATA_CONTEXT, context))

            # Stack history
            stack = self.get_stack_values()
            self.timeout(lambda: show_content(DATA_STACK, stack))

            # Watch expressions
            self.watch_expression()

        # Reload session when session stopped, by reaching end of file or interruption
        if response.get(dbgp.ATTRIBUTE_STATUS) == dbgp.STATUS_STOPPING or response.get(dbgp.ATTRIBUTE_STATUS) == dbgp.STATUS_STOPPED:
            self.run_command('xdebug_session_stop', {'restart': True})
            self.run_command('xdebug_session_start', {'restart': True})
            self.status_message('Xdebug: Finished executing file on server. Reload page to continue debugging.')

        # Render breakpoint markers
        self.timeout(lambda: render_regions())


    def get_context_values(self):
        """
        Get variables in current context.
        """
        if not is_connected():
            return

        context = H.new_dictionary()
        try:
            # Super global variables
            if self.get_option('super_globals'):
                S.SESSION.send(dbgp.CONTEXT_GET, c=1)
                response = S.SESSION.read()
                context.update(get_response_properties(response))

            # Local variables
            S.SESSION.send(dbgp.CONTEXT_GET)
            response = S.SESSION.read()
            context.update(get_response_properties(response))
        except ProtocolConnectionException:
            e = sys.exc_info()[1]
            self.timeout(lambda: connection_error("%s" % e))

        # Store context variables in session
        S.CONTEXT_DATA = context

        return generate_context_output(context)


    def get_stack_values(self):
        """
        Get stack information for current context.
        """
        response = None
        if is_connected():
            try:
                # Get stack information
                S.SESSION.send(dbgp.STACK_GET)
                response = S.SESSION.read()
            except ProtocolConnectionException:
                e = sys.exc_info()[1]
                self.timeout(lambda: connection_error("%s" % e))
        return generate_stack_output(response)


    def get_watch_values(self):
        """
        Evaluate all watch expressions in current context.
        """
        for index, item in enumerate(S.WATCH):
            # Reset value for watch expression
            S.WATCH[index]['value'] = None

            # Evaluate watch expression when connected to debugger engine
            if is_connected():
                if item['enabled']:
                    watch_value = None
                    try:
                        S.SESSION.send(dbgp.EVAL, expression=item['expression'])
                        response = S.SESSION.read()

                        watch_value = get_response_properties(response, item['expression'])
                    except ProtocolConnectionException:
                        pass

                    S.WATCH[index]['value'] = watch_value


    def init(self):
        if not is_connected():
            return

        # Connection initialization
        init = S.SESSION.read()

        # More detailed internal information on properties
        S.SESSION.send(dbgp.FEATURE_SET, n='show_hidden', v=1)
        response = S.SESSION.read()

        # Set max depth limit
        max_depth = self.get_option('max_depth', S.MAX_DEPTH)
        S.SESSION.send(dbgp.FEATURE_SET, n=dbgp.FEATURE_NAME_MAXDEPTH, v=max_depth)
        response = S.SESSION.read()

        # Set max children limit
        max_children = self.get_option('max_children', S.MAX_CHILDREN)
        S.SESSION.send(dbgp.FEATURE_SET, n=dbgp.FEATURE_NAME_MAXCHILDREN, v=max_children)
        response = S.SESSION.read()

        # Set breakpoints for files
        for filename, breakpoint_data in S.BREAKPOINT.items():
            if breakpoint_data:
                for lineno, bp in breakpoint_data.items():
                    if bp['enabled']:
                        self.set_breakpoint(filename, lineno, bp['expression'])
                        debug('breakpoint_set: ' + filename + ':' + lineno)

        # Determine if client should break at first line on connect
        if self.get_option('break_on_start'):
            # Get init attribute values
            fileuri = init.get(dbgp.INIT_FILEURI)
            filename = get_real_path(fileuri)
            # Show debug/status output
            self.status_message('Xdebug: Break on start')
            info('Break on start: ' + filename )
            # Store line number of breakpoint for displaying region marker
            S.BREAKPOINT_ROW = { 'filename': filename, 'lineno': 1 }
            # Focus/Open file window view
            self.timeout(lambda: show_file(filename, 1))

            # Context variables
            context = self.get_context_values()
            self.timeout(lambda: show_content(DATA_CONTEXT, context))

            # Stack history
            stack = self.get_stack_values()
            if not stack:
                stack = H.unicode_string('[{level}] {filename}.{where}:{lineno}\n' \
                                          .format(level=0, where='{main}', lineno=1, filename=fileuri))
            self.timeout(lambda: show_content(DATA_STACK, stack))

            # Watch expressions
            self.watch_expression()
        else:
            # Tell script to run it's process
            self.run_command('xdebug_execute', {'command': 'run'})


    def remove_breakpoint(self, breakpoint_id):
        if not breakpoint_id or not is_connected():
            return

        S.SESSION.send(dbgp.BREAKPOINT_REMOVE, d=breakpoint_id)
        response = S.SESSION.read()


    def set_breakpoint(self, filename, lineno, expression=None):
        if not filename or not lineno or not is_connected():
            return

        # Get path of file on server
        fileuri = get_real_path(filename, True)
        # Set breakpoint
        S.SESSION.send(dbgp.BREAKPOINT_SET, t='line', f=fileuri, n=lineno, expression=expression)
        response = S.SESSION.read()
        # Update breakpoint id
        breakpoint_id = response.get(dbgp.ATTRIBUTE_BREAKPOINT_ID)
        if breakpoint_id:
            S.BREAKPOINT[filename][lineno]['id'] = breakpoint_id


    def status(self):
        if not is_connected():
            return

        # Send 'status' command to debugger engine
        S.SESSION.send(dbgp.STATUS)
        response = S.SESSION.read()
        # Show response in status bar
        self.status_message("Xdebug status: " + response.get(dbgp.ATTRIBUTE_REASON) + ' - ' + response.get(dbgp.ATTRIBUTE_STATUS))


    def user_execute(self, command, args=None):
        if not command or not is_connected():
            return

        # Send command to debugger engine
        S.SESSION.send(command, args)
        response = S.SESSION.read(return_string=True)

        # Show response data in output panel
        self.timeout(lambda: show_panel_content(response))


    def watch_expression(self):
        self.get_watch_values()
        if self.get_option('has_watch_view', True):
            self.timeout(lambda: show_content(DATA_WATCH))