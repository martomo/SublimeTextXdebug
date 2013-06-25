import sublime


DEBUG = False

DEFAULT_PORT = 9000
DEFAULT_IDE_KEY = 'sublime.xdebug'

PACKAGE_PATH = None
PACKAGE_FOLDER = None

FILE_BREAKPOINT_DATA = 'Xdebug.breakpoints'
FILE_PACKAGE_SETTINGS = 'Xdebug.sublime-settings'

KEY_PROJECT_SETTINGS = 'xdebug'

REGION_KEY_BREAKPOINT = 'xdebug_breakpoint'
REGION_KEY_CURRENT = 'xdebug_current'
REGION_SCOPE_BREAKPOINT = 'comment'
REGION_SCOPE_CURRENT = 'string'

ICON_BREAKPOINT = 'circle'
ICON_BREAKPOINT_CURRENT = 'circle'
ICON_CURRENT = 'bookmark'

# Window layout for debugging output
LAYOUT_DEBUG = {
                "cols": [0.0, 0.5, 1.0],
                "rows": [0.0, 0.7, 1.0],
                "cells": [[0, 0, 2, 1], [0, 1, 1, 2], [1, 1, 2, 2]]
                }
# Default single layout (similar to Alt+Shift+1)
LAYOUT_NORMAL = {
                "cols": [0.0, 1.0],
                "rows": [0.0, 1.0],
                "cells": [[0, 0, 1, 1]]
                }

SESSION = None
BREAKPOINT = None
# Breakpoint line number in script being debugged
BREAKPOINT_ROW = None
# Will hold breakpoint line number to show for file which is being loaded
SHOW_ROW_ONLOAD = {}

CONTEXT_DATA = {}


def get_project_value(key, default_value=None):
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
    return default_value


def get_package_value(key, default_value=None):
    """
    Get value from package configuration settings.
    """
    try:
        config = sublime.load_settings(FILE_PACKAGE_SETTINGS)
        if config and config.has(key):
            return config.get(key)
    except:
        pass
    return default_value