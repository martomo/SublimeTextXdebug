DEFAULT_PORT = 9000
DEFAULT_IDE_KEY = 'sublime.xdebug'

PACKAGE_PATH = None
PACKAGE_FOLDER = None

FILE_LOG_OUTPUT = 'Xdebug.log'
FILE_BREAKPOINT_DATA = 'Xdebug.breakpoints'
FILE_PACKAGE_SETTINGS = 'Xdebug.sublime-settings'
FILE_WATCH_DATA = 'Xdebug.expressions'

KEY_SETTINGS = 'settings'
KEY_XDEBUG = 'xdebug'

KEY_PATH_MAPPING = "path_mapping"
KEY_URL = "url"
KEY_IDE_KEY = "ide_key"
KEY_PORT = "port"
KEY_SUPER_GLOBALS = "super_globals"
KEY_MAX_CHILDREN = "max_children"
KEY_MAX_DATA = "max_data"
KEY_MAX_DEPTH = "max_depth"
KEY_BREAK_ON_START = "break_on_start"
KEY_BREAK_ON_EXCEPTION = "break_on_exception"
KEY_CLOSE_ON_STOP = "close_on_stop"
KEY_HIDE_PASSWORD = "hide_password"
KEY_PRETTY_OUTPUT = "pretty_output"
KEY_LAUNCH_BROWSER = "launch_browser"
KEY_BROWSER_NO_EXECUTE = "browser_no_execute"
KEY_DISABLE_LAYOUT = "disable_layout"
KEY_DEBUG_LAYOUT = "debug_layout"

KEY_BREAKPOINT_GROUP = "breakpoint_group"
KEY_BREAKPOINT_INDEX = "breakpoint_index"
KEY_CONTEXT_GROUP = "context_group"
KEY_CONTEXT_INDEX = "context_index"
KEY_STACK_GROUP = "stack_group"
KEY_STACK_INDEX = "stack_index"
KEY_WATCH_GROUP = "watch_group"
KEY_WATCH_INDEX = "watch_index"

KEY_BREAKPOINT_CURRENT = 'breakpoint_current'
KEY_BREAKPOINT_DISABLED = 'breakpoint_disabled'
KEY_BREAKPOINT_ENABLED = 'breakpoint_enabled'
KEY_CURRENT_LINE = 'current_line'

KEY_PYTHON_PATH = "python_path"
KEY_DEBUG = "debug"

# Region scope sources
REGION_KEY_BREAKPOINT = 'xdebug_breakpoint'
REGION_KEY_CURRENT = 'xdebug_current'
REGION_KEY_DISABLED = 'xdebug_disabled'
REGION_SCOPE_BREAKPOINT = 'comment.line.settings'
REGION_SCOPE_CURRENT = 'string.quoted.settings'

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

RESTORE_LAYOUT = None
RESTORE_INDEX = None

SESSION_BUSY = False

SESSION = None
BREAKPOINT = {}
CONTEXT_DATA = {}
WATCH = []

BREAKPOINT_EXCEPTION = None
# Breakpoint line number in script being debugged
BREAKPOINT_ROW = None
# Placholder for temporary breakpoint filename and line number
BREAKPOINT_RUN = None
# Will hold breakpoint line number to show for file which is being loaded
SHOW_ROW_ONLOAD = {}

CONFIG_PROJECT = None
CONFIG_PACKAGE = None
CONFIG_KEYS = [
	KEY_PATH_MAPPING,
	KEY_URL,
	KEY_IDE_KEY,
	KEY_PORT,
	KEY_SUPER_GLOBALS,
	KEY_MAX_CHILDREN,
	KEY_MAX_DATA,
	KEY_MAX_DEPTH,
	KEY_BREAK_ON_START,
	KEY_BREAK_ON_EXCEPTION,
	KEY_CLOSE_ON_STOP,
	KEY_HIDE_PASSWORD,
	KEY_PRETTY_OUTPUT,
	KEY_LAUNCH_BROWSER,
	KEY_BROWSER_NO_EXECUTE,
	KEY_DISABLE_LAYOUT,
	KEY_DEBUG_LAYOUT,
	KEY_BREAKPOINT_GROUP,
	KEY_BREAKPOINT_INDEX,
	KEY_CONTEXT_GROUP,
	KEY_CONTEXT_INDEX,
	KEY_STACK_GROUP,
	KEY_STACK_INDEX,
	KEY_WATCH_GROUP,
	KEY_WATCH_INDEX,
	KEY_BREAKPOINT_CURRENT,
	KEY_BREAKPOINT_DISABLED,
	KEY_BREAKPOINT_ENABLED,
	KEY_CURRENT_LINE,
	KEY_PYTHON_PATH,
	KEY_DEBUG
]