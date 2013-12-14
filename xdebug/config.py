import sublime

# Settings variables
try:
    from . import settings as S
except:
    import settings as S


def load_project_values():
    try:
        settings = sublime.active_window().active_view().settings()
        # Use 'xdebug' as key which contains dictionary with project values for package
        S.CONFIG_PROJECT = settings.get(S.KEY_XDEBUG)
    except:
        pass


def load_package_values():
    # Clear previous settings
    config = {}
    try:
        # Load default/user package settings
        settings = sublime.load_settings(S.FILE_PACKAGE_SETTINGS)
        # Loop through all configuration keys
        for key in S.CONFIG_KEYS:
            # Set in config if available
            if settings and settings.has(key):
                config[key] = settings.get(key)
    except:
        pass
    # Set settings in memory
    S.CONFIG_PACKAGE = config


def get_value(key, default_value=None):
    """
    Get value from package/project configuration settings.
    """
    # Get value from project configuration
    value = get_project_value(key)
    # Use package configuration when value has not been found
    if value is None:
        value = get_package_value(key)
    # Return package/project value
    if value is not None:
        return value
    # Otherwise use default value
    return default_value


def get_package_value(key, default_value=None):
    """
    Get value from default/user package configuration settings.
    """
    try:
        config = sublime.load_settings(S.FILE_PACKAGE_SETTINGS)
        if config and config.has(key):
            return config.get(key)
    except RuntimeError:
        sublime.set_timeout(lambda: load_package_values(), 0)
        if S.CONFIG_PACKAGE:
            if key in S.CONFIG_PACKAGE:
                return S.CONFIG_PACKAGE[key]

    return default_value


def get_project_value(key, default_value=None):
    """
    Get value from project configuration settings.
    """
    # Load project coniguration settings
    try:
        load_project_values()
    except RuntimeError:
        sublime.set_timeout(lambda: load_project_values(), 0)

    # Find value in project configuration
    if S.CONFIG_PROJECT:
        if key in S.CONFIG_PROJECT:
            return S.CONFIG_PROJECT[key]

    # Otherwise use default value
    return default_value


def get_window_value(key, default_value=None):
    """
    Get value from window session settings.

    NOTE: Window object in Sublime Text 2 has no Settings.
    """
    try:
        settings = sublime.active_window().settings()
        if settings.has(S.KEY_XDEBUG):
            xdebug = settings.get(S.KEY_XDEBUG)
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
        config = sublime.load_settings(S.FILE_PACKAGE_SETTINGS)
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
    if S.KEY_SETTINGS not in project.keys() or not isinstance(project[S.KEY_SETTINGS], dict):
        project[S.KEY_SETTINGS] = {}
    if S.KEY_XDEBUG not in project[S.KEY_SETTINGS].keys() or not isinstance(project[S.KEY_SETTINGS][S.KEY_XDEBUG], dict):
        project[S.KEY_SETTINGS][S.KEY_XDEBUG] = {}
    # Update Xdebug settings
    if value is not None:
        project[S.KEY_SETTINGS][S.KEY_XDEBUG][key] = value
    elif key in project[S.KEY_SETTINGS][S.KEY_XDEBUG].keys():
        del project[S.KEY_SETTINGS][S.KEY_XDEBUG][key]
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
        if settings.has(S.KEY_XDEBUG):
            xdebug = settings.get(S.KEY_XDEBUG)
        else:
            xdebug = {}
        if value is not None:
            xdebug[key] = value
        elif key in xdebug.keys():
            del xdebug[key]
        settings.set(S.KEY_XDEBUG, xdebug)
    except:
        pass