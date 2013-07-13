import sublime

import logging
import os

# Settings variables
try:
    from . import settings as S
except:
    import settings as S

# View module
try:
    from . import view as V
except:
    import view as V

from .util import load_breakpoint_data
from .log import clear_output, info

def xdebug():
    # Clear log file
    clear_output()
    info("==== Loading %s package ====" % S.PACKAGE_FOLDER)

    # Load breakpoint data
    try:
        load_breakpoint_data()
    finally:
        # Render breakpoint markers
        V.render_regions()

    # Reset debug windows
    if sublime.active_window().get_layout() == S.LAYOUT_DEBUG:
        V.show_content(V.DATA_CONTEXT)
        V.show_content(V.DATA_BREAKPOINT)
        V.show_content(V.DATA_STACK)

    # Get package list from Package Control
    packages = None
    try:
        packages = sublime.load_settings('Package Control.sublime-settings').get('installed_packages', [])
    except:
        pass
    # Make sure it is a list
    if not isinstance(packages, list):
        packages = []
    # Get packages inside Package directory
    for package_name in os.listdir(sublime.packages_path()):
        if package_name not in packages:
            packages.append(package_name)
    # Strip .sublime-package of package name for comparison
    package_extension = ".sublime-package"
    current_package = S.PACKAGE_FOLDER
    if current_package.endswith(package_extension):
        current_package = current_package[:-len(package_extension)]
    # Check for other Xdebug packages
    duplicates = []
    for package in packages:
        if package.endswith(package_extension):
            package = package[:-len(package_extension)]
        if (package.lower().count("xdebug") or package.lower().count("moai")) and package != current_package:
            duplicates.append(package)
    # Show message if other Xdebug packages have been found
    if duplicates:
        info("Multiple 'xdebug' packages detected.")
        if not S.get_window_value('hide_conflict', False):
            sublime.error_message("The following package(s) could cause conflicts with '{package}':\n\n{other}\n\nPlease consider removing the package(s) above when experiencing any complications." \
                                    .format(package=S.PACKAGE_FOLDER, other='\n'.join(duplicates)))
            S.set_window_value('hide_conflict', True)
    else:
        S.set_window_value('hide_conflict', False)