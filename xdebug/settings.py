import sublime

DEBUG = True

DEFAULT_PORT = 9000
DEFAULT_IDE_KEY = 'sublime.xdebug'

PACKAGE_PATH = None
PACKAGE_FOLDER = None

FILE_BREAKPOINT_DATA = 'breakpoint.data'
FILE_PACKAGE_SETTINGS = 'Xdebug.sublime-settings'

KEY_PROJECT_SETTINGS = 'xdebug'

REGION_KEY_BREAKPOINT = 'xdebug_breakpoint'
REGION_KEY_CURRENT = 'xdebug_current'
REGION_SCOPE_BREAKPOINT = 'comment'
REGION_SCOPE_CURRENT = 'string'

ICON_BREAKPOINT = 'circle'
ICON_BREAKPOINT_CURRENT = 'circle'
ICON_CURRENT = 'bookmark'

SESSION = None
BREAKPOINT = None
# Breakpoint line number in script being debugged
BREAKPOINT_ROW = None


def get_project_value(key):
    """
    Get value from project configuration settings.
    """
    try:
        project = sublime.active_window().active_view().settings()
        # Use 'xdebug' as key which contains dictionary with project values for package
        config = project.get(KEY_PROJECT_SETTINGS)
        if config:
            if key in config:
                return config[key]
    except:
        pass


def get_package_value(key):
    """
    Get value from package configuration settings.
    """
    try:
        config = sublime.load_settings(FILE_PACKAGE_SETTINGS)
        if config and config.has(key):
            return config.get(key)
    except:
        pass