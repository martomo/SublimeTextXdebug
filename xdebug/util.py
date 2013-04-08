import sublime

import json
import os
import re
import sys

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


def load_breakpoint_data():
    data_path = os.path.join(S.PACKAGE_PATH, S.FILE_BREAKPOINT_DATA)
    try:
        data_file = open(data_path, 'rb')
    except:
        e = sys.exc_info()[1]
        print('Failed to open %s.\n' % data_path, e)
        return {}

    try:
        # TODO: Add Python 2.* support
        data = json.loads(data_file.read().decode('utf-8'))
    except:
        e = sys.exc_info()[1]
        print('Failed to parse %s.\n' % data_path, e)
        return {}
    return data


def save_breakpoint_data():
    #TODO: Make async
    data_path = os.path.join(S.PACKAGE_PATH, S.FILE_BREAKPOINT_DATA)
    with open(data_path, 'wb') as data:
        # TODO: Add Python 2.* support
        data.write(bytes(json.dumps(S.BREAKPOINT), 'UTF-8'))