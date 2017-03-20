import sublime

import sys
import threading

import hashlib

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

# Config module
from .config import get_value

# Log module
from .log import debug, info

# Protocol module
from .protocol import ProtocolConnectionException

# Util module
from .util import get_real_path

# View module
from .view import DATA_CONTEXT, DATA_STACK, DATA_WATCH, DATA_COROUTINES, DATA_EVALUATE, TITLE_WINDOW_WATCH, generate_context_output, generate_stack_output, generate_coroutines_output, get_response_properties, has_debug_view, render_regions, show_content, show_file, show_panel_content


ACTION_EVALUATE = "action_evaluate"
ACTION_EXECUTE = "action_execute"
ACTION_INIT = "action_init"
ACTION_REMOVE_BREAKPOINT = "action_remove_breakpoint"
ACTION_SET_BREAKPOINT = "action_set_breakpoint"
ACTION_STATUS = "action_status"
ACTION_USER_EXECUTE = "action_user_execute"
ACTION_WATCH = "action_watch"
ACTION_SET_CURRENT_STACK_LEVEL = "action_set_current_stack_level"
ACTION_SET_SELECTED_THREAD = "action_set_selected_thread"


def is_connected(show_status=False):
    """
    Check if client is connected to debugger engine.

    Keyword arguments:
    show_status -- Show message why client is not connected in status bar.
    """
    if S.PROTOCOL and S.PROTOCOL.connected:
        return True
    elif S.PROTOCOL and show_status:
        sublime.status_message('Xdebug: Waiting for response from debugger engine.')
    elif show_status:
        sublime.status_message('Xdebug: No Xdebug session running.')
    return False

def is_execution_broken():
    return S.BREAKPOINT_ROW or S.BREAKPOINT_EXCEPTION

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
        with S.PROTOCOL as protocol:
            protocol.clear()
    except:
        pass
    finally:
        S.PROTOCOL = None
        S.SESSION_BUSY = False
        S.BREAKPOINT_EXCEPTION = None
        S.BREAKPOINT_ROW = None
        S.BREAKPOINT_RUN = None
        S.CONTEXT_DATA.clear()
        async_session = SocketHandler(ACTION_WATCH)
        async_session.start()
    # Reset layout
    sublime.active_window().run_command('xdebug_layout')
    # Render breakpoint markers
    render_regions()

def update_socket_loop():
    if not S.PROTOCOL:
        return

    with S.PROTOCOL as protocol:
        protocol.update()
            
    sublime.set_timeout_async(update_socket_loop, 100)

class SocketHandler(threading.Thread):
    def __init__(self, action, **options):
        threading.Thread.__init__(self)
        self.action = action
        self.options = options
        self.current_thread = 'current' # thread currently running in Lua (since the last time execution stopped)
        self.selected_thread = 'current' # selected thread from UI
        self.current_stack_level = 1

    def get_option(self, option, default_value=None):
        if option in self.options.keys():
            return self.options[option]
        return default_value

    def run_command(self, command, args=None):
        if not isinstance(args, dict):
            args = {}
        self.timeout(lambda: self._run_command(command, args))

    def _run_command(self, command, args=None):
        try:
            sublime.active_window().run_command(command, args)
        except:
            # In case active_window() is not available
            pass

    def run_view_command(self, command, args=None):
        if not isinstance(args, dict):
            args = {}
        self.timeout(lambda: self._run_view_command)

    def _run_view_command(self, command, args=None):
        try:
            sublime.active_window().active_view().run_command(command, args)
        except:
            # In case there is no active_view() available
            pass

    def status_message(self, message):
        sublime.set_timeout(lambda: sublime.status_message(message), 100)

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
                self.evaluate(self.get_option('expression'), self.get_option('view'))
            # Execute
            elif self.action == ACTION_EXECUTE:
                self.execute(self.get_option('command'))
            # Init
            elif self.action == ACTION_INIT:
                self.init()
            # Remove breakpoint
            elif self.action == ACTION_REMOVE_BREAKPOINT:
                self.remove_breakpoint(self.get_option('filename'), self.get_option('lineno'))
            # Set breakpoint
            elif self.action == ACTION_SET_BREAKPOINT:
                # TODO: support conditional bps
                active = True # self.get_option('expression')
                self.set_breakpoint(self.get_option('filename'), self.get_option('lineno'), active)
            # Status
            elif self.action == ACTION_STATUS:
                self.status()
            # User defined execute
            elif self.action == ACTION_USER_EXECUTE:
                self.user_execute(self.get_option('command'), self.get_option('args'))
            # Watch expression
            elif self.action == ACTION_WATCH:
                self.watch_expression()
            elif self.action == ACTION_SET_CURRENT_STACK_LEVEL:
                self.set_current_stack_level(self.get_option('stack_level'))
                pass
            elif self.action == ACTION_SET_SELECTED_THREAD :
                self.set_current_stack_level(self.get_option('selected_thread'))
                pass
        # Show dialog on connection error
        except ProtocolConnectionException:
            e = sys.exc_info()[1]
            self.timeout(lambda: connection_error("%s" % e))
        finally:
            S.SESSION_BUSY = False


    def evaluate(self, expression, view):
        if not expression or not is_connected():
            return
        # Send 'eval' command to debugger engine with code to evaluate
        response = self.evaluate_expression(expression, self.current_thread, self.current_stack_level)

        transformed_response = self.transform_grld_eval_response(response)
        response_str = generate_context_output(transformed_response, values_only=True, multiline=False)

        self.timeout(lambda: view.run_command('xdebug_update_evaluate_line_response', {'response': response_str}))


    def execute(self, command):
        # Do not execute if no command is set
        if not command or not is_connected():
            return

        # Reset previous breakpoint values
        S.BREAKPOINT_EXCEPTION = None
        S.BREAKPOINT_ROW = None
        S.CONTEXT_DATA.clear()
        self.watch_expression()
        

        # Send command to debugger engine
        with S.PROTOCOL as protocol:
            protocol.send(command)

        self.run_command('xdebug_layout')
        self.timeout(lambda: render_regions())
       
    def get_value(self, grld_id):
        with S.PROTOCOL as protocol:
            protocol.send('getValue')
            protocol.send(grld_id)
            response = protocol.read()

        return response

    def is_table(self, variable):
        if type(variable) != dict: return False
        if 'value' not in variable: return False
        value = variable['value']
        if type(value) != dict: return False
        if 'type' not in value: return False

        return value['type'] == 'table'

    def transform_grld_table(self, table_variable, parent_table_refs):
        name = table_variable['name']
        table_values = table_variable['value']
        table_ref = table_values['short']
        id = table_values['id']
        type = table_values['type']
        assert type == 'table', "table_variable passed to transform_grld_table must of type 'table'"

        parent_table_refs.append(table_ref)

        table_children = self.get_value(id)
        transformed_children = {}
        for i, child in table_children.items():
            
            if self.is_table(child):
                child_table_ref = child['value']['short']
                if child_table_ref in parent_table_refs: # special value if table child is a reference to the table itself (avoid infinite recursion)
                    idx = parent_table_refs.index(child_table_ref) 
                    num_tables_up_from_child = len(parent_table_refs) - idx - 1
                    if num_tables_up_from_child == 0:
                        description = '<circular reference to this table>'
                    else:
                        description = '<circular reference to a parent table {} levels up>'.format(num_tables_up_from_child)

                    transformed_children[i] =  {'name': child['name'], 'type':'table-ref', 'value': description}
                else:
                    transformed_children[i] = self.transform_grld_variable(child, parent_table_refs)
            else:
                transformed_children[i] = self.transform_grld_variable(child, parent_table_refs)

        return {'name': name, 'type': type, 'value': table_ref, 'numchildren': len(transformed_children.keys()), 'children': transformed_children}

    def transform_grld_variable(self, variable, parent_table_refs=None):
        name = variable['name']

        # if nothing is returned, GRLD returns {name = '<no result'>}
        if not 'value' in variable:
            return {'name': '', 'value': name, 'type': ''}

        if self.is_table(variable):
            return self.transform_grld_table(variable, parent_table_refs or []) #handle tables separately

        value = variable['value']
        if type(value) == dict:
            value_type = value['type']
            value = value['short']
        else: 
            if type(value) == bool:
                value_type = 'boolean'
            elif type(value) == int or type(value) == float:
                value_type = 'number' 
            elif type(value) == str:
                value_type = 'string'
            else:
                value_type = '?' 

        return {'name': name, 'value': str(value), 'type': value_type}


    def transform_grld_eval_response(self, eval_response, scope=None):
        transformed = {}
        for i, var in eval_response.items():
            transformed_item = self.transform_grld_variable(var)

            if scope:
                name = "(%s) %s" % (scope, transformed_item['name'])
                transformed_item['name'] = name
            else:
                name = transformed_item['name']
                 
            transformed[i] = transformed_item

        return transformed


    def transform_grld_context_response(self, context_response, scope):
        return self.transform_grld_eval_response(context_response, scope)


    def get_context_values(self, thread, stack_level):
        """
        Get variables in current context.
        """
        if not is_connected():
            return

        context = H.new_dictionary()
        try:
            # local variables
            #if get_value(S.KEY_SUPER_GLOBALS):
            with S.PROTOCOL as protocol:
                protocol.send("locals")
                protocol.send(thread)
                protocol.send(stack_level)                
                response = protocol.read()
                properties = self.transform_grld_context_response(response, "local")
                context.update(properties)

                # upvalues
                protocol.send("upvalues")
                protocol.send(thread)
                protocol.send(stack_level)
                response = protocol.read()
                properties = self.transform_grld_context_response(response, "upvalue")
                context.update(properties)
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
                with S.PROTOCOL as protocol:
                    # Get stack information
                    protocol.send("callstack")
                    protocol.send(self.current_thread)
                    response = protocol.read()
            except ProtocolConnectionException:
                e = sys.exc_info()[1]
                self.timeout(lambda: connection_error("%s" % e))

        #response should be something like: {"1": {"name": <name of thing>, "namewhat": (global|local|method|field|''), "what": (Lua, C, main), "source": @<filename>, "line": line in file}}
        return response

    def evaluate_expression(self, expression, thread, stack_level):
        try:
            with S.PROTOCOL as protocol:
                protocol.send('evaluate')
                protocol.send('=' + expression) #TODO: should we always add '='?
                protocol.send(thread)
                protocol.send(stack_level)

                response = protocol.read()
        except ProtocolConnectionException:
            pass

        return response

    def get_watch_values(self, thread, stack_level):
        """
        Evaluate all watch expressions in current context.
        """

        for index, item in enumerate(S.WATCH):
            # Reset value for watch expression
            S.WATCH[index]['value'] = None

            # Evaluate watch expression when connected to debugger engine
            if is_connected():
                if item['enabled']:
                    watch_value = self.evaluate_expression(item['expression'], thread, stack_level)

                    S.WATCH[index]['value'] = self.transform_grld_eval_response(watch_value)


    def init(self):
        if not is_connected():
            return

        with S.PROTOCOL as protocol:
            protocol.register_command_cb('break', (lambda filename, line: self.handle_break_command(filename, line)))
            protocol.register_command_cb('synchronize', (lambda: self.handle_synchronize_command()))
            # Connection initialization
            client_name = protocol.read()
                
            # # Set breakpoints for files
            for filename, breakpoint_data in S.BREAKPOINT.items():
                if breakpoint_data:
                    for lineno, bp in breakpoint_data.items():
                        if bp['enabled']:
                            # TODO: support conditional bps
                            active = True #bp['expression']
                            self.set_breakpoint(filename, lineno, active)
                            debug('breakpoint_set: ' + filename + ':' + lineno)

            if get_value(S.KEY_BREAK_ON_START):
                protocol.send("break", "running")

        update_socket_loop()

    def remove_breakpoint(self, filename, lineno):
        if not is_connected():
            return

        self.set_breakpoint(filename, lineno, False)


    def set_breakpoint(self, filename, lineno, active=True):
        if not filename or not lineno or not is_connected():
            return

        with S.PROTOCOL as protocol:
            # Get path of file on server
            fileuri = get_real_path(filename, True)
            # Set breakpoint
            protocol.send("setbreakpoint", "running")
            protocol.send({"source": fileuri, "line": int(lineno), "value": active}, "running")


    def set_exception(self, exception):
        if not is_connected():
            return

        with S.PROTOCOL as protocol:
            protocol.send(dbgp.BREAKPOINT_SET, t='exception', x='"%s"' % exception)
            response = protocol.read()


    def status(self):
        if not is_connected():
            return

        with S.PROTOCOL as protocol:
            # Send 'status' command to debugger engine
            protocol.send(dbgp.STATUS)
            response = protocol.read()

        # Show response in status bar
        self.status_message("Xdebug status: " + response.get(dbgp.ATTRIBUTE_REASON) + ' - ' + response.get(dbgp.ATTRIBUTE_STATUS))


    def user_execute(self, command, args=None):
        if not command or not is_connected():
            return

        with S.PROTOCOL as protocol:
            # Send command to debugger engine
            protocol.send(command, args)
            response = protocol.read(return_string=True)

        # Show response data in output panel
        self.timeout(lambda: show_panel_content(response))


    def watch_expression(self, thread=None, stack_level=None):
        if not thread:
            thread = self.current_thread

        if not stack_level:
            stack_level = self.current_stack_level

        # Evaluate watch expressions
        self.get_watch_values(thread, stack_level)
        # Show watch expression
        self.timeout(lambda: self._watch_expression(self.get_option('check_watch_view', False)))


    def _watch_expression(self, check_watch_view):
        # Do not show if we only want to show content when Watch view is not available
        if check_watch_view and not has_debug_view(TITLE_WINDOW_WATCH):
            return

        show_content(DATA_WATCH)

    def set_current_stack_level(self, stack_level):
        self.current_stack_level = stack_level

    def set_selected_thread(self, selected_thread):
        self.selected_thread = selected_thread

    def get_all_coroutines(self):
        with S.PROTOCOL as protocol:
            protocol.send('coroutines')
            response = protocol.read()

        count = len(response.keys())
        response[count + 1] = {'id': 'main'} # always include a 'main' coroutine. This is how GRLD references the main Lua thread.

        return response


    def update_current_thread(self, coroutines_dict):
        with S.PROTOCOL as protocol:
            protocol.send('currentthread')
            current_thread = protocol.read()

        # GRLD only passes back co-routines that are NOT 'main'. So, if current_thread is not in the list, then 'main' is the current thread.    
        if current_thread not in coroutines_dict.values():
            current_thread = 'main'

        self.current_thread = current_thread

    def update_contextual_data(self, thread, stack_level):
        # Context variables
        context = self.get_context_values(thread, stack_level)
        self.timeout(lambda: show_content(DATA_CONTEXT, context))

        # Watch expressions
        self.watch_expression(thread, stack_level)

        # Render breakpoint markers
        self.timeout(lambda: render_regions())

    def handle_break_command(self, filename, line):
        S.SESSION_BUSY = True
        filename = get_real_path(filename)

        # Show debug/status output
        self.status_message('Xdebug: Break')
        info('Break: ' + filename )
        # Store line number of breakpoint for displaying region marker
        S.BREAKPOINT_ROW = { 'filename': filename, 'lineno': str(line) }

        # Focus/Open file window view
        self.timeout(lambda: show_file(filename, line))

        coroutines_dict = self.get_all_coroutines()

        self.update_current_thread(coroutines_dict)

        coroutines_str = generate_coroutines_output(coroutines_dict, self.current_thread)
        self.timeout(lambda: show_content(DATA_COROUTINES, coroutines_str))

        # Stack history
        stack = self.get_stack_values()
        if stack:
            stack_levels = [int(level) for level in stack.keys()]
            min_stack_level =  min(stack_levels)
            self.current_stack_level = min_stack_level
            stack_str = generate_stack_output(stack)
        else:
            stack_str = H.unicode_string('[{level}] {filename}.{where}:{lineno}\n' \
                                        .format(level=0, where='{main}', lineno=1, filename=fileuri))

        self.timeout(lambda: show_content(DATA_STACK, stack_str))

        self.update_contextual_data(self.current_thread, self.current_stack_level)

        S.SESSION_BUSY = False

    def handle_synchronize_command(self):
        S.SESSION_BUSY = True

        with S.PROTOCOL as protocol:
            # synchronize expects us to return the # of active breakpoints (this is actually not implemented, we MUST return 0 here)
            protocol.send(0)

            # next we need to send the "breakOnConnection" value, this is configurable, but we'll just always return false for now
            protocol.send(False)

        S.SESSION_BUSY = False
            

class SessionException(Exception):
    pass