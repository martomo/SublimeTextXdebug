import sublime
import sublime_plugin

import threading

# Load module
try:
    from .xdebug import *
except:
    from xdebug import *


class XdebugSessionStartCommand(sublime_plugin.TextCommand):
    """
    Start Xdebug session, listen for request response from debugger engine.
    """
    def run(self, edit):
        # Define new session with DBGp protocol
        S.SESSION = session.Protocol()

        # Start thread which will run method that listens for response on configured port
        threading.Thread(target=self.listen).start()

    def listen(self):
        # Start listening for response from debugger engine
        S.SESSION.listen()
        # On connect run method which handles connection
        if S.SESSION and S.SESSION.connected:
            sublime.set_timeout(self.connected, 0)

    def connected(self):
        sublime.status_message('Xdebug: Connected')
        # Connection initialization
        init = S.SESSION.read().firstChild
        # Get uri of current script file on server which is being debugged
        fileuri = init.getAttribute(dbgp.INIT_FILEURI)

        #TODO: Set breakpoints for file

        # Tell script to run it's process
        self.view.run_command('xdebug_execute', {'command': 'run'})

    def is_enabled(self):
        if S.SESSION:
            return False
        return True


class XdebugSessionStopCommand(sublime_plugin.TextCommand):
    """
    Stop Xdebug session, close connection and stop listening to debugger engine.
    """
    def run(self, edit):
        try:
            S.SESSION.clear()
        except:
            pass
        finally:
            S.SESSION = None

    def is_enabled(self):
        if S.SESSION:
            return True
        return False


class XdebugExecuteCommand(sublime_plugin.TextCommand):
    """
    Execute command, handle breakpoints and reload session when page execution has completed.

    Keyword arguments:
    command -- Command to send to debugger engine.
    """
    def run(self, edit, command=None):
        # Do not execute if no command is set
        if not command:
            sublime.status_message('Xdebug: No command')
            return

        # Send command to debugger engine
        S.SESSION.send(command)
        response = S.SESSION.read().firstChild

        # Handle breakpoint hit
        for child in response.childNodes:
            if child.nodeName == dbgp.ELEMENT_BREAKPOINT:
                print('Break: ' + child.getAttribute(dbgp.BREAKPOINT_FILENAME) + ':' + child.getAttribute(dbgp.BREAKPOINT_LINENO))
                sublime.status_message('Xdebug: Breakpoint')

        # On breakpoint get context variables and stack history
        if (response.getAttribute(dbgp.ATTRIBUTE_STATUS) == dbgp.STATUS_BREAK):
            # Local variables
            S.SESSION.send(dbgp.CONTEXT_GET)
            response = S.SESSION.read().firstChild
            context = session.get_context_values(response)

            #TODO: Get all variables by looping context_names
            print("Context variables: ", context)

            # Stack history
            S.SESSION.send(dbgp.STACK_GET)
            response = S.SESSION.read().firstChild
            stack = session.get_stack_values(response)

            print("Stack history: ", stack)

        # Reload session when session stopped, by reaching end of file or interruption
        if response.getAttribute(dbgp.ATTRIBUTE_STATUS) ==  dbgp.STATUS_STOPPING or response.getAttribute(dbgp.ATTRIBUTE_STATUS) == dbgp.STATUS_STOPPED:
            self.view.run_command('xdebug_stop_session')
            self.view.run_command('xdebug_start_session')
            sublime.status_message('Xdebug: Finished executing file on server. Reload page to continue debugging.')

    def is_enabled(self):
        return session.is_connected()


class XdebugContinueCommand(sublime_plugin.TextCommand):
    """
    Continuation commands when on breakpoint, show menu by default if no command has been passed as argument.

    Keyword arguments:
    command -- Continuation command to execute.
    """
    commands = H.new_dictionary()
    commands[dbgp.RUN] = 'Run'
    commands[dbgp.STEP_OVER] = 'Step Over'
    commands[dbgp.STEP_INTO] = 'Step Into'
    commands[dbgp.STEP_OUT] = 'Step Out'
    commands[dbgp.STOP] = 'Stop'
    commands[dbgp.DETACH] = 'Detach'

    command_index = H.dictionary_keys(commands)
    command_options = H.dictionary_values(commands)

    def run(self, edit, command=None):
        if not command or not command in self.commands:
            self.view.window().show_quick_panel(self.command_options, self.callback)
        else:
            self.callback(command)

    def callback(self, command):
        if command == -1:
            return
        if isinstance(command, int):
            command = self.command_index[command]

        self.view.run_command('xdebug_execute', {'command': command})

    def is_enabled(self):
        #TODO: Should only be enabled when breakpoint hit
        return session.is_connected()


class XdebugStatusCommand(sublime_plugin.TextCommand):
    """
    Get status from debugger engine.
    """
    def run(self, edit):
        # Send 'status' command to debugger engine
        S.SESSION.send(dbgp.STATUS)
        response = S.SESSION.read().firstChild
        # Show response in status bar
        sublime.status_message("Xdebug status: " + response.getAttribute(dbgp.ATTRIBUTE_REASON) + ' - ' + response.getAttribute(dbgp.ATTRIBUTE_STATUS))

    def is_enabled(self):
        return session.is_connected()


class XdebugUserExecuteCommand(sublime_plugin.TextCommand):
    """
    Open input panel, allowing user to execute arbitrary command according to DBGp protocol.
    Note: Transaction ID is automatically generated by session class.
    """
    def run(self, edit):
        self.view.window().show_input_panel('Xdebug execute', '', self.on_done, self.on_change, self.on_cancel)

    def on_done(self, line):
        # Split command and arguments, define arguments when only command is defined.
        if ' ' in line:
            command, args = line.split(' ', 1)
        else:
            command, args = line, ''

        # Send command to debugger engine
        S.SESSION.send(command, args)
        response = S.SESSION.read().firstChild

        # Show output panel
        window = self.view.window()
        if window is None:
            return
        window.run_command('show_panel', {'panel': 'output.xdebug_execute'})

        # Show response data in output panel
        output = window.get_output_panel('xdebug_execute')
        if output is None:
            return
        output.run_command('xdebug_view_update', {'data': response.toprettyxml()})

    def on_change(self, line):
        pass

    def on_cancel(self):
        pass

    def is_enabled(self):
        return session.is_connected()


class XdebugViewUpdateCommand(sublime_plugin.TextCommand):
    """
    Update content of sublime.Edit object in view, instead of using begin_edit/end_edit.

    Keyword arguments:
    data -- Content data to populate sublime.Edit object with.
    readonly -- Make sublime.Edit object read only.
    """
    def run(self, edit, data=None, readonly=False):
        v = self.view
        v.set_read_only(False)
        v.erase(edit, sublime.Region(0, v.size()))
        if not data is None:
            v.insert(edit, 0, data)
        if readonly:
            v.set_read_only(True)