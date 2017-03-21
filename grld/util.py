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

    #filename = try_get_local_path_from_mounted_paths(uri)
    filename = filename.replace('@', '') # remove lua @ which represents "a file" as opposed to something run inline/from a REPL

    # Normalize path for comparison and remove duplicate/trailing slashes
    uri = os.path.normpath(filename)

    # Pattern for checking if uri is a windows path
    windows_pattern = re.compile('.*\\.*')

    # Prepend leading slash if filesystem is not Windows
    if not windows_pattern.match(uri) and not os.path.isabs(uri):
        uri = os.path.normpath('/' + uri)

    path_mapping = get_value(S.KEY_PATH_MAPPING)
    if isinstance(path_mapping, dict):

        found_path_mapping = False
        
        # Go through path mappings
        for server_path, local_path in path_mapping.items():
            server_path = os.path.normpath(server_path)
            local_path = os.path.normpath(local_path)
            # Replace path if mapping available
            if server:
                # Map local path to server path
                if local_path in uri:
                    uri = uri.replace(local_path, server_path)
                    found_path_mapping = True
                    break
            else:
                # Map server path to local path
                if server_path in uri:
                    uri = uri.replace(server_path, local_path)
                    found_path_mapping = True
                    break

        # "=[C]" is a special case url for lua C code
        if not found_path_mapping and uri != '=[C]':
            server_or_local = 'server' if server else 'local'
            sublime.set_timeout(lambda: sublime.error_message("GRLD: No {} path mapping defined for path {}. It's likely that your breakpoints for this file won't be hit! You can set up path mappings in the SublimeTextGRLD package settings.".format(server_or_local, uri)), 0)
    else:
        sublime.set_timeout(lambda: sublime.status_message("GRLD: No path mapping defined, returning given path."), 100)

    # special transformations for server paths (GRLD expects this)
    if server:
        uri = uri.replace("\\", "/")
        uri = os.path.join("./", uri)
        uri = "@{}".format(uri)

    # Append scheme
    #if server:
        #return H.url_encode("file://" + uri)

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
            # ST3: Packages/GRLD Client/icons/breakpoint_enabled.png
            icon_path = "Packages/" + current_package + '/icons/{0}.png'
        else:
            # ST2: ../GRLD Client/icons/breakpoint_enabled
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
