import os
import sublime
import threading
from urllib import request
from urllib.parse import urlencode
from unittesting import DeferrableTestCase


class XdebugDeferrableTestCase(DeferrableTestCase):
    # Using realpath in order to resolve any symbolic links otherwise path mapping will not work
    package_path = os.environ.get('TRAVIS_BUILD_DIR', os.path.realpath(os.path.join(sublime.packages_path(), 'SublimeTextXdebug')))
    platform = os.environ.get('TRAVIS_OS_NAME', 'docker')

    local_path = os.path.join(package_path, 'tests', 'server', 'public')
    remote_path = local_path if platform == 'osx' else '/var/www/html'
    server_host = '127.0.0.1:8090'

    project_data = {
        'folders': [
            {'path': local_path}
        ],
        'settings': {
            # Ensure Sublime Text window remains opened at all times
            'close_windows_when_empty': False,
            # Force tabs in order to properly assert content
            'translate_tabs_to_spaces': False,
            # Specify default settings in case of running tests locally,
            # to prevent failure with defined (conflicting) user settings
            'xdebug': {
                'path_mapping': {},
                'url': '',
                'ide_key': 'sublime.xdebug',
                'host': '',
                'port': 9000,
                'max_children': 32,
                'max_data': 1024,
                'max_depth': 1,
                'break_on_start': False,
                'break_on_exception': [
                    'Fatal error',
                    'Catchable fatal error',
                    'Warning',
                    'Parse error',
                    'Notice',
                    'Strict standards',
                    'Deprecated',
                    'Xdebug',
                    'Unknown error'
                ],
                'close_on_stop': False,
                'super_globals': True,
                'fullname_property': True,
                'hide_password': False,
                'pretty_output': False,
                'launch_browser': False,
                'browser_no_execute': False,
                'disable_layout': False,
                'debug_layout': {
                    'cols': [0.0, 0.5, 1.0],
                    'rows': [0.0, 0.7, 1.0],
                    'cells': [[0, 0, 2, 1], [0, 1, 1, 2], [1, 1, 2, 2]]
                },
                'breakpoint_group': 2,
                'breakpoint_index': 1,
                'context_group': 1,
                'context_index': 0,
                'stack_group': 2,
                'stack_index': 0,
                'watch_group': 1,
                'watch_index': 1,
                'breakpoint_enabled': 'circle',
                'breakpoint_disabled': 'dot',
                'breakpoint_current': '',
                'current_line': 'bookmark',
                'python_path': '',
                'debug': False
            }
        }
    }

    # Path mapping is only required when server is on a remote machine.
    # Most cases test server is started in Docker (using php-server),
    # with the exception of macOS on Travis CI and will be running locally.
    if remote_path != local_path:
        project_data['settings']['xdebug']['path_mapping'] = {
            remote_path: local_path
        }

    def setUp(self):
        self._xdebug_settings = {}

        project_data = self.project_data.copy()
        project_data['settings']['xdebug']['_testMethodName'] = self._testMethodName
        sublime.active_window().set_project_data(project_data)

        def has_loaded_project_data():
            return self.get_xdebug_setting('_testMethodName') == self._testMethodName
        yield has_loaded_project_data

    def tearDown(self):
        # Stop active session to prevent multiple test cases listening to port 9000
        self.run_command('xdebug_session_stop')
        # Remove any breakpoints to ensure a clean slate
        self.run_command('xdebug_clear_all_breakpoints')
        # Restore layout and close any files opened during session
        self.run_command('xdebug_layout', {'restore': True})
        self.run_command('close_all')

    def assertViewContains(self, view, content):
        if not self.view_contains_content(view, content):
            title = 'View'
            if isinstance(view, sublime.View):
                title = view.name() if view.name() else view.file_name()
            self.fail(title + ' does not contain "' + content + '".')

    def assertViewIsEmpty(self, view):
        if not self.view_is_empty(view):
            title = 'View'
            if isinstance(view, sublime.View):
                title = view.name() if view.name() else view.file_name()
            self.fail(title + ' is not empty.')

    def get_contents_of_view(self, view):
        if view:
            return view.substr(sublime.Region(0, view.size()))
        return ''

    def get_view_by_title(self, title):
        for view in sublime.active_window().views():
            if view.name() == title or view.file_name() == title:
                return view
        return None

    def get_xdebug_setting(self, key):
        settings = sublime.active_window().active_view().settings().get('xdebug')
        if isinstance(settings, dict) and key in settings:
            return settings[key]
        return None

    def run_command(self, *args, **kwargs):
        sublime.active_window().run_command(*args, **kwargs)

    def send_server_request(self, path='', params='XDEBUG_SESSION_START=1'):
        if isinstance(params, dict):
            params = urlencode(params)
        query_string = '?' + params if len(params) else ''
        url = 'http://{host}/{path}{query_string}'.format(host=self.server_host, path=path, query_string=query_string)
        # Send request to server in separate thread to prevent blocking of test execution
        threading.Thread(target=request.urlopen, args=(url,)).start()
        print('Request send to {url}'.format(url=url))

    def set_breakpoint(self, filename, lineno, enabled=True):
        self.run_command('xdebug_breakpoint', {'enabled': enabled, 'filename': filename, 'rows': [str(lineno)]})

    def set_xdebug_settings(self, settings):
        project_data = sublime.active_window().project_data()
        for key, value in settings.items():
            if value is not None:
                project_data['settings']['xdebug'][key] = value
            elif key in project_data['settings']['xdebug'].keys():
                del project_data['settings']['xdebug'][key]
            # Remember any user defined settings for Xdebug plugin,
            # which are to be validated in 'window_has_xdebug_settings'
            self._xdebug_settings[key] = value
        sublime.active_window().set_project_data(project_data)

    def view_contains_content(self, view, content):
        view_contents = self.get_contents_of_view(view)
        return content in view_contents

    def view_is_empty(self, view):
        view_contents = self.get_contents_of_view(view)
        return not view_contents

    def window_has_debug_layout(self):
        for view in sublime.active_window().views():
            # Watch view is last to initialize
            if view.name() == 'Xdebug Watch':
                return True
        return False

    def window_has_xdebug_settings(self):
        for key, value in self._xdebug_settings.items():
            if self.get_xdebug_setting(key) != value:
                return False
        return True
