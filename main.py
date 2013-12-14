import sublime
import sublime_plugin

import os
import sys
import threading

# Load modules
try:
    from .xdebug import *
except:
    from xdebug import *

# Set Python libraries from system installation
python_path = config.get_value(S.KEY_PYTHON_PATH)
if python_path:
    python_path = os.path.normpath(python_path.replace("\\", "/"))
    python_dynload = os.path.join(python_path, 'lib-dynload')
    if python_dynload not in sys.path:
        sys.path.append(python_dynload)

# Define path variables
try:
    S.PACKAGE_PATH = os.path.dirname(os.path.realpath(__file__))
    S.PACKAGE_FOLDER = os.path.basename(S.PACKAGE_PATH)
except:
    pass


# Initialize package
sublime.set_timeout(lambda: load.xdebug(), 1000)


# Define event listener for view(s)
class EventListener(sublime_plugin.EventListener):
    def on_load(self, view):
        filename = view.file_name()
        # Scroll the view to current breakpoint line
        if filename and filename in S.SHOW_ROW_ONLOAD:
            V.show_at_row(view, S.SHOW_ROW_ONLOAD[filename])
            del S.SHOW_ROW_ONLOAD[filename]
        # Render breakpoint markers
        sublime.set_timeout(lambda: V.render_regions(view), 0)

    def on_activated(self, view):
        # Render breakpoint markers
        V.render_regions(view)

    def on_post_save(self, view):
        filename = view.file_name()
        # Render breakpoint markers
        V.render_regions(view)
        # Update config when settings file or sublime-project has been saved
        if filename and (filename.endswith(S.FILE_PACKAGE_SETTINGS) or filename.endswith('.sublime-project')):
            config.load_package_values()
            config.load_project_values()
        #TODO: Save new location of breakpoints on save

    def on_selection_modified(self, view):
        # Show details in output panel of selected variable in context window
        if view.name() == V.TITLE_WINDOW_CONTEXT:
            V.show_context_output(view)
        elif view.name() == V.TITLE_WINDOW_BREAKPOINT:
            V.toggle_breakpoint(view)
        elif view.name() == V.TITLE_WINDOW_STACK:
            V.toggle_stack(view)
        elif view.name() == V.TITLE_WINDOW_WATCH:
            V.toggle_watch(view)
        else:
            pass


class XdebugBreakpointCommand(sublime_plugin.TextCommand):
    """
    Add/Remove breakpoint(s) for rows (line numbers) in selection.
    """
    def run(self, edit, rows=None, condition=None, enabled=None, filename=None):
        # Get filename in current view and check if is a valid filename
        if filename is None:
            filename = self.view.file_name()
        if not filename or not os.path.isfile(filename):
            return

        # Add entry for file in breakpoint data
        if filename not in S.BREAKPOINT:
            S.BREAKPOINT[filename] = {}

        # When no rows are defined, use selected rows (line numbers), filtering empty rows
        if rows is None:
            rows = V.region_to_rows(self.view.sel(), filter_empty=True)

        # Loop through rows
        for row in rows:
            expression = None
            if condition is not None and len(condition.strip()) > 0:
                expression = condition
            # Check if breakpoint exists
            breakpoint_exists = row in S.BREAKPOINT[filename]
            # Disable/Remove breakpoint
            if breakpoint_exists:
                if S.BREAKPOINT[filename][row]['id'] is not None and session.is_connected(show_status=True):
                    async_session = session.SocketHandler(session.ACTION_REMOVE_BREAKPOINT, breakpoint_id=S.BREAKPOINT[filename][row]['id'])
                    async_session.start()
                if enabled is False:
                    S.BREAKPOINT[filename][row]['enabled'] = False
                elif enabled is None:
                    del S.BREAKPOINT[filename][row]
            # Add/Enable breakpoint
            if not breakpoint_exists or enabled is True:
                if row not in S.BREAKPOINT[filename]:
                    S.BREAKPOINT[filename][row] = { 'id': None, 'enabled': True, 'expression': expression }
                else:
                    S.BREAKPOINT[filename][row]['enabled'] = True
                    if condition is not None:
                        S.BREAKPOINT[filename][row]['expression'] = expression
                    else:
                        expression = S.BREAKPOINT[filename][row]['expression']
                if session.is_connected(show_status=True):
                    async_session = session.SocketHandler(session.ACTION_SET_BREAKPOINT, filename=filename, lineno=row, expression=expression)
                    async_session.start()

        # Render breakpoint markers
        V.render_regions()

        # Update breakpoint list
        try:
            if V.has_debug_view(V.TITLE_WINDOW_BREAKPOINT):
                V.show_content(V.DATA_BREAKPOINT)
        except:
            pass

        # Save breakpoint data to file
        util.save_breakpoint_data()


class XdebugConditionalBreakpointCommand(sublime_plugin.TextCommand):
    """
    Add conditional breakpoint(s) for rows (line numbers) in selection.
    """
    def run(self, edit):
        self.view.window().show_input_panel('Breakpoint condition', '', self.on_done, self.on_change, self.on_cancel)

    def on_done(self, condition):
        self.view.run_command('xdebug_breakpoint', {'condition': condition, 'enabled': True})

    def on_change(self, line):
        pass

    def on_cancel(self):
        pass


class XdebugClearBreakpointsCommand(sublime_plugin.TextCommand):
    """
    Clear breakpoints in selected view.
    """
    def run(self, edit):
        filename = self.view.file_name()
        if filename and filename in S.BREAKPOINT:
            rows = H.dictionary_keys(S.BREAKPOINT[filename])
            self.view.run_command('xdebug_breakpoint', {'rows': rows, 'filename': filename})
            # Continue debug session when breakpoints are cleared on current script being debugged
            if S.BREAKPOINT_ROW and self.view.file_name() == S.BREAKPOINT_ROW['filename']:
                self.view.window().run_command('xdebug_execute', {'command': 'run'})

    def is_enabled(self):
        filename = self.view.file_name()
        if filename and S.BREAKPOINT and filename in S.BREAKPOINT and S.BREAKPOINT[filename]:
            return True
        return False

    def is_visible(self):
        filename = self.view.file_name()
        if filename and S.BREAKPOINT and filename in S.BREAKPOINT and S.BREAKPOINT[filename]:
            return True
        return False


class XdebugClearAllBreakpointsCommand(sublime_plugin.WindowCommand):
    """
    Clear breakpoints from all views.
    """
    def run(self):
        view = sublime.active_window().active_view()
        # Unable to run to line when no view available
        if view is None:
            return

        for filename, breakpoint_data in S.BREAKPOINT.items():
            if breakpoint_data:
                rows = H.dictionary_keys(breakpoint_data)
                view.run_command('xdebug_breakpoint', {'rows': rows, 'filename': filename})
        # Continue debug session when breakpoints are cleared on current script being debugged
        self.window.run_command('xdebug_execute', {'command': 'run'})

    def is_enabled(self):
        if S.BREAKPOINT:
            for filename, breakpoint_data in S.BREAKPOINT.items():
                if breakpoint_data:
                    return True
        return False

    def is_visible(self):
        if S.BREAKPOINT:
            for filename, breakpoint_data in S.BREAKPOINT.items():
                if breakpoint_data:
                    return True
        return False


class XdebugRunToLineCommand(sublime_plugin.WindowCommand):
    """
    Run script to current selected line in view, ignoring all other breakpoints.
    """
    def run(self):
        view = sublime.active_window().active_view()
        # Unable to run to line when no view available
        if view is None:
            return
        # Determine filename for current view and check if is a valid filename
        filename = view.file_name()
        if not filename or not os.path.isfile(filename):
            return
        # Get first line from selected rows and make sure it is not empty
        rows = V.region_to_rows(filter_empty=True)
        if rows is None or len(rows) == 0:
            return
        lineno = rows[0]
        # Check if breakpoint does not already exists
        breakpoint_exists = False
        if filename in S.BREAKPOINT and lineno in S.BREAKPOINT[filename]:
            breakpoint_exists = True
        # Store line number and filename for temporary breakpoint in session
        if not breakpoint_exists:
            S.BREAKPOINT_RUN = { 'filename': filename, 'lineno': lineno }
        # Set breakpoint and run script
        view.run_command('xdebug_breakpoint', {'rows': [lineno], 'enabled': True, 'filename': filename})
        self.window.run_command('xdebug_execute', {'command': 'run'})

    def is_enabled(self):
        return S.BREAKPOINT_ROW is not None and session.is_connected()

    def is_visible(self):
        return S.BREAKPOINT_ROW is not None and session.is_connected()


class XdebugSessionStartCommand(sublime_plugin.WindowCommand):
    """
    Start Xdebug session, listen for request response from debugger engine.
    """
    def run(self, launch_browser=False, restart=False):
        # Define new session with DBGp protocol
        S.SESSION = protocol.Protocol()
        S.SESSION_BUSY = False
        S.BREAKPOINT_EXCEPTION = None
        S.BREAKPOINT_ROW = None
        S.CONTEXT_DATA.clear()
        async_session = session.SocketHandler(session.ACTION_WATCH, check_watch_view=True)
        async_session.start()
        # Remove temporary breakpoint
        if S.BREAKPOINT_RUN is not None and S.BREAKPOINT_RUN['filename'] in S.BREAKPOINT and S.BREAKPOINT_RUN['lineno'] in S.BREAKPOINT[S.BREAKPOINT_RUN['filename']]:
            self.window.active_view().run_command('xdebug_breakpoint', {'rows': [S.BREAKPOINT_RUN['lineno']], 'filename': S.BREAKPOINT_RUN['filename']})
        S.BREAKPOINT_RUN = None
        # Set debug layout
        self.window.run_command('xdebug_layout')
        # Launch browser
        if launch_browser or (config.get_value(S.KEY_LAUNCH_BROWSER) and not restart):
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
        sublime.set_timeout(lambda: sublime.status_message('Xdebug: Connected'), 100)

        async_session = session.SocketHandler(session.ACTION_INIT)
        async_session.start()

    def is_enabled(self):
        if S.SESSION:
            return False
        return True

    def is_visible(self, launch_browser=False):
        if S.SESSION:
            return False
        if launch_browser and (config.get_value(S.KEY_LAUNCH_BROWSER) or not config.get_value(S.KEY_URL)):
            return False
        return True


class XdebugSessionRestartCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.run_command('xdebug_session_stop', {'restart': True})
        self.window.run_command('xdebug_session_start', {'restart': True})
        sublime.set_timeout(lambda: sublime.status_message('Xdebug: Restarted debugging session. Reload page to continue debugging.'), 100)

    def is_enabled(self):
        if S.SESSION:
            return True
        return False

    def is_visible(self):
        if S.SESSION:
            return True
        return False


class XdebugSessionStopCommand(sublime_plugin.WindowCommand):
    """
    Stop Xdebug session, close connection and stop listening to debugger engine.
    """
    def run(self, close_windows=False, launch_browser=False, restart=False):
        try:
            S.SESSION.clear()
        except:
            pass
        finally:
            S.SESSION = None
            S.SESSION_BUSY = False
            S.BREAKPOINT_EXCEPTION = None
            S.BREAKPOINT_ROW = None
            S.CONTEXT_DATA.clear()
            async_session = session.SocketHandler(session.ACTION_WATCH, check_watch_view=True)
            async_session.start()
            # Remove temporary breakpoint
            if S.BREAKPOINT_RUN is not None and S.BREAKPOINT_RUN['filename'] in S.BREAKPOINT and S.BREAKPOINT_RUN['lineno'] in S.BREAKPOINT[S.BREAKPOINT_RUN['filename']]:
                self.window.active_view().run_command('xdebug_breakpoint', {'rows': [S.BREAKPOINT_RUN['lineno']], 'filename': S.BREAKPOINT_RUN['filename']})
            S.BREAKPOINT_RUN = None
        # Launch browser
        if launch_browser or (config.get_value(S.KEY_LAUNCH_BROWSER) and not restart):
            util.launch_browser()
        # Close or reset debug layout
        if close_windows or config.get_value(S.KEY_CLOSE_ON_STOP):
            if config.get_value(S.KEY_DISABLE_LAYOUT):
                self.window.run_command('xdebug_layout', {'close_windows': True})
            else:
                self.window.run_command('xdebug_layout', {'restore': True})
        else:
            self.window.run_command('xdebug_layout')
        # Render breakpoint markers
        V.render_regions()

    def is_enabled(self):
        if S.SESSION:
            return True
        return False

    def is_visible(self, close_windows=False, launch_browser=False):
        if S.SESSION:
            if close_windows and config.get_value(S.KEY_CLOSE_ON_STOP):
                return False
            if launch_browser and (config.get_value(S.KEY_LAUNCH_BROWSER) or not config.get_value(S.KEY_URL)):
                return False
            return True
        return False


class XdebugExecuteCommand(sublime_plugin.WindowCommand):
    """
    Execute command, handle breakpoints and reload session when page execution has completed.

    Keyword arguments:
    command -- Command to send to debugger engine.
    """
    def run(self, command=None):
        async_session = session.SocketHandler(session.ACTION_EXECUTE, command=command)
        async_session.start()

    def is_enabled(self):
        return session.is_connected()


class XdebugContinueCommand(sublime_plugin.WindowCommand):
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

    def run(self, command=None):
        if not command or not command in self.commands:
            self.window.show_quick_panel(self.command_options, self.callback)
        else:
            self.callback(command)

    def callback(self, command):
        if command == -1 or S.SESSION_BUSY:
            return
        if isinstance(command, int):
            command = self.command_index[command]

        self.window.run_command('xdebug_execute', {'command': command})

    def is_enabled(self):
        return S.BREAKPOINT_ROW is not None and session.is_connected()

    def is_visible(self):
        return S.BREAKPOINT_ROW is not None and session.is_connected()


class XdebugStatusCommand(sublime_plugin.WindowCommand):
    """
    Get status from debugger engine.
    """
    def run(self):
        async_session = session.SocketHandler(session.ACTION_STATUS)
        async_session.start()

    def is_enabled(self):
        return session.is_connected()

    def is_visible(self):
        return session.is_connected()


class XdebugEvaluateCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.show_input_panel('Evaluate', '', self.on_done, self.on_change, self.on_cancel)

    def on_done(self, expression):
        async_session = session.SocketHandler(session.ACTION_EVALUATE, expression=expression)
        async_session.start()

    def on_change(self, expression):
        pass

    def on_cancel(self):
        pass

    def is_enabled(self):
        return session.is_connected()

    def is_visible(self):
        return session.is_connected()


class XdebugUserExecuteCommand(sublime_plugin.WindowCommand):
    """
    Open input panel, allowing user to execute arbitrary command according to DBGp protocol.
    Note: Transaction ID is automatically generated by session module.
    """
    def run(self):
        self.window.show_input_panel('DBGp command', '', self.on_done, self.on_change, self.on_cancel)

    def on_done(self, line):
        # Split command and arguments, define arguments when only command is defined.
        if ' ' in line:
            command, args = line.split(' ', 1)
        else:
            command, args = line, ''

        async_session = session.SocketHandler(session.ACTION_USER_EXECUTE, command=command, args=args)
        async_session.start()

    def on_change(self, line):
        pass

    def on_cancel(self):
        pass

    def is_enabled(self):
        return session.is_connected()

    def is_visible(self):
        return session.is_connected()


class XdebugWatchCommand(sublime_plugin.WindowCommand):
    """
    Add/Edit/Remove watch expression.
    """
    def run(self, clear=False, edit=False, remove=False, update=False):
        self.edit = edit
        self.remove = remove
        self.watch_index = None
        # Clear watch expressions in list
        if clear:
            try:
                # Python 3.3+
                S.WATCH.clear()
            except AttributeError:
                del S.WATCH[:]
            # Update watch view
            self.update_view()
        # Edit or remove watch expression
        elif edit or remove:
            # Generate list with available watch expressions
            watch_options = []
            for index, item in enumerate(S.WATCH):
                watch_item = '[{status}] - {expression}'.format(index=index, expression=item['expression'], status='enabled' if item['enabled'] else 'disabled')
                watch_options.append(watch_item)
            self.window.show_quick_panel(watch_options, self.callback)
        elif update:
            self.update_view()
        # Set watch expression
        else:
            self.set_expression()

    def callback(self, index):
        # User has cancelled action
        if index == -1:
            return
        # Make sure index is valid integer
        if isinstance(index, int) or H.is_digit(index):
            self.watch_index = int(index)
            # Edit watch expression
            if self.edit:
                self.set_expression()
            # Remove watch expression
            else:
                S.WATCH.pop(self.watch_index)
                # Update watch view
                self.update_view()

    def on_done(self, expression):
        # User did not set expression
        if not expression:
            return
        # Check if expression is not already defined
        matches = [x for x in S.WATCH if x['expression'] == expression]
        if matches:
            sublime.status_message('Xdebug: Watch expression already defined.')
            return
        # Add/Edit watch expression in session
        watch = {'expression': expression, 'enabled': True, 'value': None, 'type': None}
        if self.watch_index is not None and isinstance(self.watch_index, int):
            try:
                S.WATCH[self.watch_index]['expression'] = expression
            except:
                S.WATCH.insert(self.watch_index, watch)
        else:
            S.WATCH.append(watch)
        # Update watch view
        self.update_view()

    def on_change(self, line):
        pass

    def on_cancel(self):
        pass

    def set_expression(self):
        # Show user input for setting watch expression
        self.window.show_input_panel('Watch expression', '', self.on_done, self.on_change, self.on_cancel)

    def update_view(self):
        async_session = session.SocketHandler(session.ACTION_WATCH, check_watch_view=True)
        async_session.start()
        # Save watch data to file
        util.save_watch_data()

    def is_visible(self, clear=False, edit=False, remove=False):
        if (clear or edit or remove) and not S.WATCH:
            return False
        return True


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
        if data is not None:
            view.insert(edit, 0, data)
        if readonly:
            view.set_read_only(True)


class XdebugLayoutCommand(sublime_plugin.WindowCommand):
    """
    Toggle between debug and default window layouts.
    """
    def run(self, restore=False, close_windows=False, keymap=False):
        # Get active window
        window = sublime.active_window()
        # Do not restore layout or close windows while debugging
        if S.SESSION and (restore or close_windows or keymap):
            return
        # Set layout, unless user disabled debug layout
        if not config.get_value(S.KEY_DISABLE_LAYOUT):
            if restore or keymap:
                V.set_layout('normal')
            else:
                V.set_layout('debug')
        # Close all debugging related windows
        if close_windows or restore or keymap:
            V.close_debug_windows()
            return
        # Reset data in debugging related windows
        V.show_content(V.DATA_BREAKPOINT)
        V.show_content(V.DATA_CONTEXT)
        V.show_content(V.DATA_STACK)
        V.show_content(V.DATA_WATCH)
        panel = window.get_output_panel('xdebug')
        panel.run_command("xdebug_view_update")
        # Close output panel
        window.run_command('hide_panel', {"panel": 'output.xdebug'})

    def is_enabled(self, restore=False, close_windows=False):
        disable_layout = config.get_value(S.KEY_DISABLE_LAYOUT)
        if close_windows and (not disable_layout or not V.has_debug_view()):
            return False
        if restore and disable_layout:
            return False
        return True

    def is_visible(self, restore=False, close_windows=False):
        if S.SESSION:
            return False
        disable_layout = config.get_value(S.KEY_DISABLE_LAYOUT)
        if close_windows and (not disable_layout or not V.has_debug_view()):
            return False
        if restore and disable_layout:
            return False
        if restore:
            try:
                return sublime.active_window().get_layout() == config.get_value(S.KEY_DEBUG_LAYOUT, S.LAYOUT_DEBUG)
            except:
                pass
        return True


class XdebugSettingsCommand(sublime_plugin.WindowCommand):
    """
    Show settings file.
    """
    def run(self, default=True):
        # Show default settings in package when available
        if default and S.PACKAGE_FOLDER is not None:
            package = S.PACKAGE_FOLDER
        # Otherwise show User defined settings
        else:
            package = "User"
        # Strip .sublime-package of package name for syntax file
        package_extension = ".sublime-package"
        if package.endswith(package_extension):
            package = package[:-len(package_extension)]
        # Open settings file
        self.window.run_command('open_file', {'file': '${packages}/' + package + '/' + S.FILE_PACKAGE_SETTINGS });