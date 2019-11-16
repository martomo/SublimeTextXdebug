import os
import sublime
from unittesting import DeferrableTestCase

# Using realpath in order to resolve any symbolic links otherwise path mapping will not work
package_path = os.environ.get('TRAVIS_BUILD_DIR', os.path.realpath(os.path.join(sublime.packages_path(), 'SublimeTextXdebug')))
server_path = os.path.join(package_path, 'tests', 'server', 'public')


class DeferrableXdebugTestCase(DeferrableTestCase):

    def setUpClass():
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
        platform = os.environ.get('TRAVIS_OS_NAME', 'docker')
        if not platform == 'osx':
            project_data['settings']['xdebug']['path_mapping'] = {
                '/var/www/html/': server_path
            }

        sublime.active_window().set_project_data(project_data)

    def assertViewContains(self, view, content):
        if not self.view_contains_content(view, content):
            title = 'View'
            if isinstance(view, sublime.View):
                title = view.name() if view.name() else view.file_name()
            self.fail(title + ' does not contain "' + content + '".')
