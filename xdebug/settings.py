# Module which has Global variables

import sublime

DEBUG = True

DEFAULT_PORT = 9000
DEFAULT_IDE_KEY = 'sublime.xdebug'

SESSION = None
BUFFER = {}


def get_project_value(key):
    """
    Get value from project configuration settings.
    """
    try:
        s = sublime.active_window().active_view().settings()
        # Use 'xdebug' as key which contains dictionary with project values for package
        xdebug = s.get('xdebug')
        if xdebug:
            if key in xdebug:
                return xdebug[key]
    except:
        pass


def get_package_value(key):
    """
    Get value from package configuration settings.
    """
    try:
    	s = sublime.load_settings("Xdebug.sublime-settings")
    	if s and s.has(key):
       		return s.get(key)
    except:
    	pass