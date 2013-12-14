import sublime

import json
import os
import re
import sys
import webbrowser

# Helper module
try:
    from .helper import H
except:
    from helper import H

# Settings variables
try:
    from . import settings as S
except:
    import settings as S

# Config module
from .config import get_value

# Log module
from .log import debug, info


def get_real_path(uri, server=False):
    """
    Get real path

    Keyword arguments:
    uri -- Uri of file that needs to be mapped and located
    server -- Map local path to server path

    TODO: Fix mapping for root (/) and drive letters (P:/)
    """
    if uri is None:
        return uri

    # URLdecode uri
    uri = H.url_decode(uri)

    # Split scheme from uri to get absolute path
    try:
        # scheme:///path/file => scheme, /path/file
        # scheme:///C:/path/file => scheme, C:/path/file
        transport, filename = uri.split(':///', 1) 
    except:
        filename = uri

    # Normalize path for comparison and remove duplicate/trailing slashes
    uri = os.path.normpath(filename)

    # Pattern for checking if uri is a windows path
    drive_pattern = re.compile(r'^[a-zA-Z]:[\\/]')

    # Append leading slash if filesystem is not Windows
    if not drive_pattern.match(uri) and not os.path.isabs(uri):
        uri = os.path.normpath('/' + uri)

    path_mapping = get_value(S.KEY_PATH_MAPPING)
    if isinstance(path_mapping, dict):
        # Go through path mappings
        for server_path, local_path in path_mapping.items():
            server_path = os.path.normpath(server_path)
            local_path = os.path.normpath(local_path)
            # Replace path if mapping available
            if server:
                # Map local path to server path
                if local_path in uri:
                    uri = uri.replace(local_path, server_path)
                    break
            else:
                # Map server path to local path
                if server_path in uri:
                    uri = uri.replace(server_path, local_path)
                    break
    else:
        sublime.set_timeout(lambda: sublime.status_message("Xdebug: No path mapping defined, returning given path."), 100)

    # Replace slashes
    if not drive_pattern.match(uri):
        uri = uri.replace("\\", "/")

    # Append scheme
    if server:
        return H.url_encode("file://" + uri)

    return uri


def get_region_icon(icon):
    # Default icons for color schemes from default theme
    default_current = 'bookmark'
    default_disabled = 'dot'
    default_enabled = 'circle'

    # Package icons (without .png extension)
    package_breakpoint_current = 'breakpoint_current'
    package_breakpoint_disabled = 'breakpoint_disabled'
    package_breakpoint_enabled = 'breakpoint_enabled'
    package_current_line = 'current_line'

    # List to check for duplicate icon entries
    icon_list = [default_current, default_disabled, default_enabled]

    # Determine icon path
    icon_path = None
    if S.PACKAGE_FOLDER is not None:
        # Strip .sublime-package of package name for comparison
        package_extension = ".sublime-package"
        current_package = S.PACKAGE_FOLDER
        if current_package.endswith(package_extension):
            current_package = current_package[:-len(package_extension)]
        if sublime.version() == '' or int(sublime.version()) > 3000:
            # ST3: Packages/Xdebug Client/icons/breakpoint_enabled.png
            icon_path = "Packages/" + current_package + '/icons/{0}.png'
        else:
            # ST2: ../Xdebug Client/icons/breakpoint_enabled
            icon_path = "../" + current_package + '/icons/{0}'
        # Append icon path to package icons
        package_breakpoint_current = icon_path.format(package_breakpoint_current)
        package_breakpoint_disabled = icon_path.format(package_breakpoint_disabled)
        package_breakpoint_enabled = icon_path.format(package_breakpoint_enabled)
        package_current_line = icon_path.format(package_current_line)
        # Add to duplicate list
        icon_list.append(icon_path.format(package_breakpoint_current))
        icon_list.append(icon_path.format(package_breakpoint_disabled))
        icon_list.append(icon_path.format(package_breakpoint_enabled))
        icon_list.append(icon_path.format(package_current_line))

    # Get user defined icons from settings
    breakpoint_current = get_value(S.KEY_BREAKPOINT_CURRENT)
    breakpoint_disabled = get_value(S.KEY_BREAKPOINT_DISABLED)
    breakpoint_enabled = get_value(S.KEY_BREAKPOINT_ENABLED)
    current_line = get_value(S.KEY_CURRENT_LINE)

    # Duplicate check, enabled breakpoint
    if breakpoint_enabled not in icon_list:
        icon_list.append(breakpoint_enabled)
    else:
        breakpoint_enabled = None
    # Duplicate check, disabled breakpoint
    if breakpoint_disabled not in icon_list:
        icon_list.append(breakpoint_disabled)
    else:
        breakpoint_disabled = None
    # Duplicate check, current line
    if current_line not in icon_list:
        icon_list.append(current_line)
    else:
        current_line = None
    # Duplicate check, current breakpoint
    if breakpoint_current not in icon_list:
        icon_list.append(breakpoint_current)
    else:
        breakpoint_current = None

    # Use default/package icon if no user defined or duplicate detected
    if not breakpoint_current and icon_path is not None:
        breakpoint_current = package_breakpoint_current
    if not breakpoint_disabled:
        breakpoint_disabled = default_disabled if icon_path is None else package_breakpoint_disabled
    if not breakpoint_enabled:
        breakpoint_enabled = default_enabled if icon_path is None else package_breakpoint_enabled
    if not current_line:
        current_line = default_current if icon_path is None else package_current_line

    # Return icon for icon name
    if icon == S.KEY_CURRENT_LINE:
        return current_line
    elif icon == S.KEY_BREAKPOINT_CURRENT:
        return breakpoint_current
    elif icon == S.KEY_BREAKPOINT_DISABLED:
        return breakpoint_disabled
    elif icon == S.KEY_BREAKPOINT_ENABLED:
        return breakpoint_enabled
    else:
        info("Invalid icon name. (" + icon + ")")
        return


def launch_browser():
    url = get_value(S.KEY_URL)
    if not url:
        sublime.set_timeout(lambda: sublime.status_message('Xdebug: No URL defined in (project) settings file.'), 100)
        return
    ide_key = get_value(S.KEY_IDE_KEY, S.DEFAULT_IDE_KEY)
    operator = '?'

    # Check if url already has query string
    if url.count("?"):
        operator = '&'

    # Start debug session
    if S.SESSION and (S.SESSION.listening or not S.SESSION.connected):
        webbrowser.open(url + operator + 'XDEBUG_SESSION_START=' + ide_key)
    # Stop debug session
    else:
        # Check if we should execute script
        if get_value(S.KEY_BROWSER_NO_EXECUTE):
            # Without executing script
            webbrowser.open(url + operator + 'XDEBUG_SESSION_STOP_NO_EXEC=' + ide_key)
        else:
            # Run script normally
            webbrowser.open(url + operator + 'XDEBUG_SESSION_STOP=' + ide_key)


def load_breakpoint_data():
    data_path = os.path.join(sublime.packages_path(), 'User', S.FILE_BREAKPOINT_DATA)
    data = {}
    try:
        data_file = open(data_path, 'rb')
    except:
        e = sys.exc_info()[1]
        info('Failed to open %s.' % data_path)
        debug(e)

    try:
        data = json.loads(H.data_read(data_file.read()))
    except:
        e = sys.exc_info()[1]
        info('Failed to parse %s.' % data_path)
        debug(e)

    # Do not use deleted files or entries without breakpoints
    if data:
        for filename, breakpoint_data in data.copy().items():
            if not breakpoint_data or not os.path.isfile(filename):
                del data[filename]

    if not isinstance(S.BREAKPOINT, dict):
        S.BREAKPOINT = {}

    # Set breakpoint data
    S.BREAKPOINT.update(data)


def load_watch_data():
    data_path = os.path.join(sublime.packages_path(), 'User', S.FILE_WATCH_DATA)
    data = []
    try:
        data_file = open(data_path, 'rb')
    except:
        e = sys.exc_info()[1]
        info('Failed to open %s.' % data_path)
        debug(e)

    try:
        data = json.loads(H.data_read(data_file.read()))
    except:
        e = sys.exc_info()[1]
        info('Failed to parse %s.' % data_path)
        debug(e)

    # Check if expression is not already defined
    duplicates = []
    for index, entry in enumerate(data):
        matches = [x for x in S.WATCH if x['expression'] == entry['expression']]
        if matches:
            duplicates.append(entry)
        else:
            # Unset any previous value
            data[index]['value'] = None
    for duplicate in duplicates:
        data.remove(duplicate)

    if not isinstance(S.WATCH, list):
        S.WATCH = []

    # Set watch data
    S.WATCH.extend(data)


def save_breakpoint_data():
    data_path = os.path.join(sublime.packages_path(), 'User', S.FILE_BREAKPOINT_DATA)
    with open(data_path, 'wb') as data:
        data.write(H.data_write(json.dumps(S.BREAKPOINT)))


def save_watch_data():
    data_path = os.path.join(sublime.packages_path(), 'User', S.FILE_WATCH_DATA)
    with open(data_path, 'wb') as data:
        data.write(H.data_write(json.dumps(S.WATCH)))