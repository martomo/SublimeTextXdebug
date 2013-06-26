import sublime
import sublime_plugin

import os
import threading


# Load modules
try:
    from .xdebug import *
except:
    from xdebug import *


# Define path variables
try:
    S.PACKAGE_PATH = os.path.dirname(os.path.realpath(__file__))
    S.PACKAGE_FOLDER = os.path.basename(S.PACKAGE_PATH)
except:
    print("Unable to resolve current path for package.")


# Load breakpoint data
if S.BREAKPOINT is None:
    S.BREAKPOINT = {}
    sublime.set_timeout(lambda: util.load_breakpoint_data(), 1000)


# Define event listener for view(s)
class EventListener(sublime_plugin.EventListener):
    def on_load(self, view):
        filename = view.file_name()
        # Create settings template upon opening empty settings file
        if filename and filename.endswith(S.FILE_PACKAGE_SETTINGS) and not view.size() > 0:
            view.run_command("xdebug_view_update", {'data': util.generate_settings() })
        # Scroll the view to current breakpoint line
        if filename and filename in S.SHOW_ROW_ONLOAD:
            V.show_at_row(view, S.SHOW_ROW_ONLOAD[filename])
            del S.SHOW_ROW_ONLOAD[filename]

    def on_activated(self, view):
        # Render breakpoint markers
        V.render_regions(view)

    def on_post_save(self, view):
        # Render breakpoint markers
        V.render_regions(view)
        #TODO: Save new location of breakpoints on save

    def on_selection_modified(self, view):
        # Show details in output panel of selected variable in context window
        if view.name() == V.TITLE_WINDOW_CONTEXT:
            V.show_context_output(view)
        else:
            pass


class XdebugBreakpointCommand(sublime_plugin.TextCommand):
    """
    Add/Remove breakpoint(s) for rows (line numbers) in selection.

    TODO: By argument setting expression for conditional breakpoint
    """
    def run(self, edit, rows=None, expression=None):
        # Get filename in current view and check if is a valid filename
        filename = self.view.file_name()
        if not filename:
            return

        # Add entry for file in breakpoint data
        if filename not in S.BREAKPOINT:
            S.BREAKPOINT[filename] = {}

        # When no rows are defined, use selected rows (line numbers), filtering empty rows
        if rows is None:
            rows = V.region_to_rows(self.view.sel(), filter_empty=True)

        # Loop through rows
        for row in rows:
            # Add breakpoint
            if row not in S.BREAKPOINT[filename]:
                S.BREAKPOINT[filename][row] = { 'id': None, 'enabled': True, 'expression': expression }
                if session.is_connected():
                    S.SESSION.send(dbgp.BREAKPOINT_SET, t='line', f=util.get_real_path(filename, True), n=row)
                    response = S.SESSION.read().firstChild
                    breakpoint_id = response.getAttribute('id')
                    if breakpoint_id:
                        S.BREAKPOINT[filename][row]['id'] = breakpoint_id
            # Remove breakpoint
            else:
                if session.is_connected() and S.BREAKPOINT[filename][row]['id'] is not None:
                    S.SESSION.send(dbgp.BREAKPOINT_REMOVE, d=S.BREAKPOINT[filename][row]['id'])
                    response = S.SESSION.read().firstChild
                del S.BREAKPOINT[filename][row]

        # Render breakpoint markers
        V.render_regions()

        # Save breakpoint data to file
        util.save_breakpoint_data()


class XdebugClearBreakpointsCommand(sublime_plugin.TextCommand):
    """
    Clear all breakpoints in selected view.
    """
    def run(self, edit):
        filename = self.view.file_name()
        if filename and filename in S.BREAKPOINT:
            rows = H.dictionary_keys(S.BREAKPOINT[filename])
            self.view.run_command('xdebug_breakpoint', {'rows': rows})
            # Continue debug process after clearing breakpoints
            self.view.run_command('xdebug_execute', {'command': 'run'})


class XdebugSessionStartCommand(sublime_plugin.TextCommand):
    """
    Start Xdebug session, listen for request response from debugger engine.
    """
    def run(self, edit, launch_browser=False):
        # Define new session with DBGp protocol
        S.SESSION = session.Protocol()
        S.BREAKPOINT_ROW = None
        S.CONTEXT_DATA.clear()
        self.view.run_command('xdebug_reset_layout', {'layout': 'debug'})
        if launch_browser:
            util.launch_browser()

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

        # Set breakpoints for files
        for filename, breakpoint_data in S.BREAKPOINT.items():
            if breakpoint_data:
                # Get path of file on server
                fileuri = util.get_real_path(filename, True)
                for lineno, bp in breakpoint_data.items():
                    if bp['enabled']:
                        S.SESSION.send(dbgp.BREAKPOINT_SET, t='line', f=fileuri, n=lineno, expression=bp['expression'])
                        response = S.SESSION.read().firstChild
                        # Update breakpoint id
                        breakpoint_id = response.getAttribute('id')
                        if breakpoint_id:
                            S.BREAKPOINT[filename][lineno]['id'] = breakpoint_id
                        if S.DEBUG: print('breakpoint_set: ' + filename + ':' + lineno)

        # Tell script to run it's process
        self.view.run_command('xdebug_execute', {'command': 'run'})

    def is_enabled(self):
        if S.SESSION:
            return False
        return True

    def is_visible(self, launch_browser=False):
        if S.SESSION:
            return False
        if launch_browser and not (S.get_project_value('url') or S.get_package_value('url')):
            return False
        return True


class XdebugSessionStopCommand(sublime_plugin.TextCommand):
    """
    Stop Xdebug session, close connection and stop listening to debugger engine.
    """
    def run(self, edit, close_windows=False, launch_browser=False):
        if launch_browser:
            util.launch_browser()
        try:
            S.SESSION.clear()
        except:
            pass
        finally:
            S.SESSION = None
            S.BREAKPOINT_ROW = None
            S.CONTEXT_DATA.clear()
        if close_windows:
            self.view.run_command('xdebug_reset_layout', {'layout': 'default'})
        else:
            self.view.run_command('xdebug_reset_layout', {'layout': 'debug'})
        # Render breakpoint markers
        V.render_regions()

    def is_enabled(self):
        if S.SESSION:
            return True
        return False

    def is_visible(self, launch_browser=False):
        if S.SESSION:
            if launch_browser and not (S.get_project_value('url') or S.get_package_value('url')):
                return False
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

        # Reset previous breakpoint values
        S.BREAKPOINT_ROW = None
        S.CONTEXT_DATA.clear()
        self.view.run_command('xdebug_reset_layout', {'layout': 'debug'})

        # Handle breakpoint hit
        for child in response.childNodes:
            if child.nodeName == dbgp.ELEMENT_BREAKPOINT:
                sublime.status_message('Xdebug: Breakpoint')
                # Get breakpoint attribute values
                fileuri = child.getAttribute(dbgp.BREAKPOINT_FILENAME)
                lineno = child.getAttribute(dbgp.BREAKPOINT_LINENO)
                filename = util.get_real_path(fileuri)
                # Show debug output
                if S.DEBUG: print('Break: ' + filename + ':' + lineno)
                # Store line number of breakpoint for displaying region marker
                S.BREAKPOINT_ROW = { 'filename': filename, 'lineno': lineno }
                # Focus/Open file window view
                V.show_file(filename, lineno)


        # On breakpoint get context variables and stack history
        if (response.getAttribute(dbgp.ATTRIBUTE_STATUS) == dbgp.STATUS_BREAK):
            # Context variables
            context = session.get_context_values()
            V.show_content(V.DATA_CONTEXT, context)

            # Stack history
            stack = session.get_stack_values()
            V.show_content(V.DATA_STACK, stack)

        # Reload session when session stopped, by reaching end of file or interruption
        if response.getAttribute(dbgp.ATTRIBUTE_STATUS) ==  dbgp.STATUS_STOPPING or response.getAttribute(dbgp.ATTRIBUTE_STATUS) == dbgp.STATUS_STOPPED:
            self.view.run_command('xdebug_session_stop')
            self.view.run_command('xdebug_session_start')
            sublime.status_message('Xdebug: Finished executing file on server. Reload page to continue debugging.')

        # Render breakpoint markers
        V.render_regions()

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
        return S.BREAKPOINT_ROW is not None and session.is_connected()

    def is_visible(self):
        return S.BREAKPOINT_ROW is not None and session.is_connected()


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

    def is_visible(self):
        return session.is_connected()


class XdebugUserExecuteCommand(sublime_plugin.TextCommand):
    """
    Open input panel, allowing user to execute arbitrary command according to DBGp protocol.
    Note: Transaction ID is automatically generated by session module.
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

    def is_visible(self):
        return session.is_connected()


class XdebugViewUpdateCommand(sublime_plugin.TextCommand):
    """
    Update content of sublime.Edit object in view, instead of using begin_edit/end_edit.

    Keyword arguments:
    data -- Content data to populate sublime.Edit object with.
    readonly -- Make sublime.Edit object read only.
    """
    def run(self, edit, data=None, readonly=False):
        view = self.view
        view.set_read_only(False)
        view.erase(edit, sublime.Region(0, view.size()))
        if not data is None:
            view.insert(edit, 0, data)
        if readonly:
            view.set_read_only(True)


class XdebugResetLayoutCommand(sublime_plugin.TextCommand):
    """
    Toggle between debug and default window layouts.
    """
    def run(self, edit, layout='default', keymap=False):
        # Get active window
        window = sublime.active_window()
        # Check keymap
        if keymap and (S.SESSION or window.get_layout() != S.LAYOUT_DEBUG):
            return
        # Set layout
        V.set_layout(layout)
        # Only execute following when debugging
        if not layout == 'debug':
            return
        # Reset data in debugging related windows
        V.show_content(V.DATA_CONTEXT)
        V.show_content(V.DATA_STACK)
        output = window.get_output_panel('xdebug_inspect')
        output.run_command("xdebug_view_update")
        # Close output panel
        window.run_command('hide_panel', {"panel": 'output.xdebug_inspect'})

    def is_visible(self):
        if S.SESSION:
            return False
        try:
            return sublime.active_window().get_layout() == S.LAYOUT_DEBUG
        except:
            return True