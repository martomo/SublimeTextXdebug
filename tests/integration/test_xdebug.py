import os
import sublime
import threading
from urllib import request
from unittesting import DeferrableTestCase

# Using realpath in order to resolve any symbolic links otherwise path mapping will not work
package_path = os.environ.get('TRAVIS_BUILD_DIR', os.path.realpath(os.path.join(sublime.packages_path(), 'SublimeTextXdebug')))
platform = os.environ.get('TRAVIS_OS_NAME', 'docker')
server_path = os.path.join(package_path, 'tests', 'server', 'public')
remote_path = server_path if platform == 'osx' else '/var/www/html'
version = sublime.version()


class TestXdebug(DeferrableTestCase):

    def setUpClass():
        print(version)

        settings = sublime.load_settings('Preferences.sublime-settings')
        # Ensure Sublime Text window remains opened at all times
        settings.set('close_windows_when_empty', False)

        project_data = {
            'folders': [
                {'path': server_path}
            ],
            'settings': {
                # Force tabs in order to properly assert content
                'translate_tabs_to_spaces': False,
                'xdebug': {
                    'debug': True
                }
            }
        }

        # Path mapping is only required when server is on a remote machine.
        # Most cases test server is started in Docker (using php-server),
        # with the exception of macOS on Travis CI and will be running locally.
        if remote_path != server_path:
            project_data['settings']['xdebug']['path_mapping'] = {
                remote_path: server_path
            }

        sublime.active_window().set_project_data(project_data)
        print(sublime.active_window().project_data())

    def assertViewContains(self, view, content):
        print('assertViewContains', content)
        if not self.view_contains_content(view, content):
            title = 'View'
            if isinstance(view, sublime.View):
                title = view.name() if view.name() else view.file_name()
            self.fail(title + ' does not contain "' + content + '".')
        print('all good')

    def get_contents_of_view(self, view):
        if view:
            return view.substr(sublime.Region(0, view.size()))
        return ''

    def get_view_by_title(self, title):
        window = sublime.active_window()
        for view in window.views():
            if view.name() == title or view.file_name() == title:
                return view

    def send_get_request(self, file=''):
        url = 'http://127.0.0.1:8090/%s?XDEBUG_SESSION_START=1' % file
        print(url)
        threading.Thread(target=request.urlopen, args=(url,)).start()

    def set_breakpoint(self, filename, lineno, enabled=True):
        window = sublime.active_window()
        window.run_command('xdebug_breakpoint', {'enabled': enabled, 'filename': filename, 'rows': [str(lineno)]})

    def view_has_contents(self, view):
        view_contents = self.get_contents_of_view(view)
        return len(view_contents) > 0

    def view_contains_content(self, view, content):
        view_contents = self.get_contents_of_view(view)
        return content in view_contents

    def window_has_debug_layout(self):
        print('window_has_debug_layout')
        window = sublime.active_window()
        for view in window.views():
            # Watch view is last to initialize
            if view.name() == 'Xdebug Watch':
                return True
        return False

    def test_xdebug(self):
        window = sublime.active_window()
        index_file = os.path.join(server_path, 'index.php')

        print('breakpoint')
        self.set_breakpoint(index_file, 3)

        print('start')
        window.run_command('xdebug_session_start')

        yield self.window_has_debug_layout

        print('views')
        views = window.views()
        for index, view in enumerate(views):
            view_contents = view.substr(sublime.Region(0, view.size()))
            print(view.id(), view.name(), view.file_name())
            print(view_contents)

        breakpoint_view = self.get_view_by_title('Xdebug Breakpoint')
        context_view = self.get_view_by_title('Xdebug Context')
        stack_view = self.get_view_by_title('Xdebug Stack')

        print('assert breakpoint')
        self.assertViewContains(breakpoint_view, '=> ' + index_file + '\n\t|+| 3')

        print('request')
        self.send_get_request()

        def context_and_stack_have_content():
            print('context_and_stack_have_content')
            return self.view_has_contents(context_view) and self.view_has_contents(stack_view)

        yield context_and_stack_have_content

        print('views')
        views = window.views()
        for index, view in enumerate(views):
            view_contents = view.substr(sublime.Region(0, view.size()))
            print(view.id(), view.name(), view.file_name())
            print(view_contents)

        print('assert context')
        self.assertViewContains(context_view, '$hello = <uninitialized>')
        print('assert stack')
        self.assertViewContains(stack_view, '[0] file://%s/index.php:3, {main}()' % remote_path)

        context_view_contents = self.get_contents_of_view(context_view)
        stack_view_contents = self.get_contents_of_view(stack_view)

        def context_and_stack_have_different_content():
            print('context_and_stack_have_different_content')
            return self.get_contents_of_view(context_view) != context_view_contents and self.get_contents_of_view(stack_view) != stack_view_contents

        print('step_into')
        window.run_command('xdebug_execute', {'command': 'step_into'})
        yield context_and_stack_have_different_content
        yield context_and_stack_have_content

        print('assert context')
        self.assertViewContains(context_view, '$hello = (string) world')
        print('assert stack')
        self.assertViewContains(stack_view, '[0] file://%s/index.php:4, {main}()' % remote_path)

        print('stop')
        window.run_command('xdebug_session_stop')
