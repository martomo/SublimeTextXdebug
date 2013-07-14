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

    path_mapping = S.get_project_value('path_mapping') or S.get_package_value('path_mapping')
    if not path_mapping is None:
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
        sublime.status_message("Xdebug: No path mapping defined, returning given path.")

    # Replace slashes
    if not drive_pattern.match(uri):
        uri = uri.replace("\\", "/")

    # Append scheme
    if server:
        return H.url_encode("file://" + uri)

    return uri


def generate_settings():
    settings = {}
    settings["port"] = S.DEFAULT_PORT
    settings["ide_key"] = S.DEFAULT_IDE_KEY
    settings["url"] = ""
    settings["path_mapping"] = {}
    return json.dumps(settings, indent = 4)


def launch_browser():
    url = S.get_project_value('url') or S.get_package_value('url')
    if not url:
        sublime.status_message('Xdebug: No URL defined in (project) settings file.')
        return
    ide_key = S.get_project_value('ide_key') or S.get_package_value('ide_key') or S.DEFAULT_IDE_KEY

    if S.SESSION and (S.SESSION.listening or not S.SESSION.connected):
        webbrowser.open(url + '?XDEBUG_SESSION_START=' + ide_key)
    else:
        webbrowser.open(url + '?XDEBUG_SESSION_STOP=' + ide_key)


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


def save_breakpoint_data():
    data_path = os.path.join(sublime.packages_path(), 'User', S.FILE_BREAKPOINT_DATA)
    with open(data_path, 'wb') as data:
        data.write(H.data_write(json.dumps(S.BREAKPOINT)))