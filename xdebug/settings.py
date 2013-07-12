import sublime

DEBUG = False

DEFAULT_PORT = 9000
DEFAULT_IDE_KEY = 'sublime.xdebug'

PACKAGE_PATH = None
PACKAGE_FOLDER = None

FILE_LOG_OUTPUT = 'Xdebug.log'
FILE_BREAKPOINT_DATA = 'Xdebug.breakpoints'
FILE_PACKAGE_SETTINGS = 'Xdebug.sublime-settings'

KEY_SETTINGS = 'settings'
KEY_XDEBUG = 'xdebug'

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
CLOSE_ON_STOP = False

RESTORE_LAYOUT = None
RESTORE_INDEX = None

SESSION = None
BREAKPOINT = {}
CONTEXT_DATA = {}

# Breakpoint line number in script being debugged
BREAKPOINT_ROW = None
# Will hold breakpoint line number to show for file which is being loaded
SHOW_ROW_ONLOAD = {}

# Maximum amount of array children and object's properties to return
MAX_CHILDREN = 0
# Maximum amount of nested levels to retrieve of array elements and object properties
MAX_DEPTH = 1023


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


def get_project_value(key, default_value=None):
    """
    Get value from project configuration settings.
    """
    try:
        project = sublime.active_window().active_view().settings()
        # Use 'xdebug' as key which contains dictionary with project values for package
        config = project.get(KEY_XDEBUG)
        if config:
            if key in config:
                return config[key]
    except:
        pass
    return default_value


def get_window_value(key, default_value=None):
    """
    Get value from window session settings.

    NOTE: Window object in Sublime Text 2 has no Settings.
    """
    try:
        settings = sublime.active_window().settings()
        if settings.has(KEY_XDEBUG):
            xdebug = settings.get(KEY_XDEBUG)
            if isinstance(xdebug, dict) and key in xdebug.keys():
                return xdebug[key]
    except:
        pass
    return default_value


def set_package_value(key, value=None):
    """
    Set value in package configuration settings.
    """
    try:
        config = sublime.load_settings(FILE_PACKAGE_SETTINGS)
        if value is not None:
            config.set(key, value)
        elif config and config.has(key):
            return config.erase(key)
    except:
        pass


def set_project_value(key, value=None):
    """
    Set value in project configuration settings.
    """
    # Unable to set project value if no project file
    if not sublime.active_window().project_file_name():
        return False
    # Get current project data
    project = sublime.active_window().project_data()
    # Make sure project data is a dictionary
    if not isinstance(project, dict):
        project = {}
    # Create settings entries if they are undefined
    if KEY_SETTINGS not in project.keys() or not isinstance(project[KEY_SETTINGS], dict):
        project[KEY_SETTINGS] = {}
    if KEY_XDEBUG not in project[KEY_SETTINGS].keys() or not isinstance(project[KEY_SETTINGS][KEY_XDEBUG], dict):
        project[KEY_SETTINGS][KEY_XDEBUG] = {}
    # Update Xdebug settings
    if value is not None:
        project[KEY_SETTINGS][KEY_XDEBUG][key] = value
    elif key in project[KEY_SETTINGS][KEY_XDEBUG].keys():
        del project[KEY_SETTINGS][KEY_XDEBUG][key]
    # Save project data
    sublime.active_window().set_project_data(project)
    return True


def set_window_value(key, value=None):
    """
    Set value in window session settings.

    NOTE: Window object in Sublime Text 2 has no Settings.
    """
    try:
        settings = sublime.active_window().settings()
        if settings.has(KEY_XDEBUG):
            xdebug = settings.get(KEY_XDEBUG)
        else:
            xdebug = {}
        if value is not None:
            xdebug[key] = value
        elif key in xdebug.keys():
            del xdebug[key]
        settings.set(KEY_XDEBUG, xdebug)
    except:
        pass