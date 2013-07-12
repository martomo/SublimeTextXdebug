import sublime

import os
import re

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

# Session module
try:
    from . import session
except:
    import session


DATA_BREAKPOINT = 'breakpoint'
DATA_CONTEXT = 'context'
DATA_STACK = 'stack'

TITLE_WINDOW_BREAKPOINT = "Xdebug Breakpoint"
TITLE_WINDOW_CONTEXT = "Xdebug Context"
TITLE_WINDOW_STACK = "Xdebug Stack"


def set_layout(layout):
    """
    Toggle between debug and default window layouts.
    """
    # Get active window and set reference to active view
    window = sublime.active_window()
    previous_active = window.active_view()

    # Show debug layout
    if layout == 'debug':
        if window.get_layout() != S.LAYOUT_DEBUG:
            # Save current layout
            restore_layout = window.get_layout()
            S.set_window_value('restore_layout', restore_layout)
            # Remember view indexes
            restore_index = H.new_dictionary()
            for view in window.views():
                view_id = "%d" % view.id()
                group, index = window.get_view_index(view)
                restore_index[view_id] = { "group": group, "index": index }
            S.set_window_value('restore_index', restore_index)
            # Set debug layout
            window.set_layout(S.LAYOUT_NORMAL)
        window.set_layout(S.LAYOUT_DEBUG)
    # Show previous (single) layout
    else:
        # Get previous layout configuration
        restore_layout = S.get_window_value('restore_layout', S.LAYOUT_NORMAL)
        restore_index = S.get_window_value('restore_index', {})
        # Restore layout
        window.set_layout(S.LAYOUT_NORMAL)
        window.set_layout(restore_layout)
        for view in window.views():
            view_id = "%d" % view.id()
            # Set view indexes
            if view_id in H.dictionary_keys(restore_index):
                v = restore_index[view_id]
                window.set_view_index(view, v["group"], v["index"])
            # Close all debugging related windows
            if view.name() == TITLE_WINDOW_BREAKPOINT or view.name() == TITLE_WINDOW_CONTEXT or view.name() == TITLE_WINDOW_STACK:
                window.focus_view(view)
                window.run_command('close')
        window.run_command('hide_panel', {"panel": 'output.xdebug_inspect'})

    # Restore focus to previous active view
    if not previous_active is None:
        window.focus_view(previous_active)


def show_context_output(view):
    """
    Show selected variable in an output panel when clicked in context window.

    Keyword arguments:
    view -- View reference which holds the context window.
    """
    # Check if there is a debug session and context data
    if S.SESSION and S.SESSION.connected and S.CONTEXT_DATA:
        try:
            # Get selected point in view
            point = view.sel()[0].a
            # Check if selected point uses variable scope
            if sublime.score_selector(view.scope_name(point), 'variable'):
                # Find variable in line which contains the point
                line = view.substr(view.line(point))
                pattern = re.compile('^\\s*(\\$.*?)\\s+\\=')
                match = pattern.match(line)
                if match:
                    # Get variable details from context data
                    variable_name = match.group(1)
                    variable = session.get_context_variable(S.CONTEXT_DATA, variable_name)
                    if variable:
                        # Convert details to text output
                        variables = H.new_dictionary()
                        variables[variable_name] = variable
                        data = session.generate_context_output(variables)
                        # Show context variables and children in output panel
                        window = sublime.active_window()
                        output = window.get_output_panel('xdebug_inspect')
                        output.run_command("xdebug_view_update", {'data' : data} )
                        output.run_command('set_setting', {"setting": 'word_wrap', "value": True})
                        window.run_command('show_panel', {"panel": 'output.xdebug_inspect'})
        except:
            pass


def show_content(data, content=None):
    """
    Show content for specific data type in assigned window view.
    Note: When view does not exists, it will create one.
    """
    # Get active window and set reference to active view
    window = sublime.active_window()
    previous_active = window.active_view_in_group(0)

    # Determine data type
    if data == DATA_CONTEXT:
        group = 1
        title = TITLE_WINDOW_CONTEXT
    if data == DATA_STACK:
        group = 2
        title = TITLE_WINDOW_STACK
    if data == DATA_BREAKPOINT:
        group = 2
        title = TITLE_WINDOW_BREAKPOINT
        content = session.get_breakpoint_values()

    # Search for view assigned to data type
    found = False
    view = None
    for view in window.views():
        if view.name() == title:
            found = True
            # Make sure the view is in the right group
            view_group, view_index = window.get_view_index(view)
            if view_group != group:
                window.set_view_index(view, group, 0)
            break

    # Create new view if it does not exists
    if not found:
        view = window.new_file()
        view.set_scratch(True)
        view.set_read_only(True)
        view.set_name(title)
        view.settings().set('word_wrap', False)
        if S.PACKAGE_FOLDER and os.path.exists(S.PACKAGE_PATH + "/Xdebug.tmLanguage"):
            view.set_syntax_file("Packages/" + S.PACKAGE_FOLDER + "/Xdebug.tmLanguage")
        window.set_view_index(view, group, 0)

    # Set content for view and fold all indendation blocks
    view.run_command('xdebug_view_update', {'data': content, 'readonly': True})
    view.run_command('fold_all')

    # Restore focus to previous active view/group
    if not previous_active is None:
        window.focus_view(previous_active)
    else:
        window.focus_group(0)


def show_file(filename, row=None):
    """
    Open or focus file in window, which is currently being debugged.

    Keyword arguments:
    filename -- Absolute path of file on local device.
    """
    # Check if file exists if being referred to file system
    if os.path.exists(filename):
        # Get active window
        window = sublime.active_window()
        window.focus_group(0)
        # Check if file is already open
        found = False
        view = window.find_open_file(filename)
        if not view is None:
            found = True
            window.focus_view(view)
            # Set focus to row (line number)
            show_at_row(view, row)
        # Open file if not open
        if not found:
            view = window.open_file(filename)
            window.focus_view(view)
            # Set focus to row (line number) when file is loaded
            S.SHOW_ROW_ONLOAD[filename] = row


def show_at_row(view, row=None):
    """
    Scroll the view to center on the given row (line number).

    Keyword arguments:
    - view -- Which view to scroll to center on row.
    - row -- Row where to center the view.
    """
    if row is not None:
        try:
            # Convert row (line number) to region
            row_region = rows_to_region(row)[0].a
            # Scroll the view to row
            view.show_at_center(row_region)
        except:
            # When defining row_region index could be out of bounds
            pass


def rows_to_region(rows):
    """
    Convert rows (line numbers) to a region (selection/cursor position).

    Keyword arguments:
    - rows -- Row number(s) to convert to region(s).
    """

    # Get current active view
    view = sublime.active_window().active_view()

    # List for containing regions to return
    region = []

    # Create list if it is a singleton
    if not isinstance(rows, list):
        rows = [rows]

    for row in rows:
        # Check if row is a digit
        if isinstance(row, int) or H.is_digit(row):
            # Convert from 1 based to a 0 based row (line) number
            row_number = int(row) - 1
            # Calculate offset point for row
            offset_point = view.text_point(row_number, 0)
            # Get region for row by offset point
            region_row = view.line(offset_point)
            # Add to list for result
            region.append(region_row)

    return region


def region_to_rows(region=None, filter_empty=False):
    """
    Convert a region (selection/cursor position) to rows (line numbers).

    Keyword arguments:
    - region -- sublime.Selection/sublime.RegionSet or sublime.Region to convert to row number(s).
    - filter_empty -- Filter empty rows (line numbers).
    """

    # Get current active view
    view = sublime.active_window().active_view()

    # Use current selection/cursor position if no region defined
    if region is None:
        region = view.sel()

    # List for containing rows (line numbers) to return
    rows = []

    # Create list if it is a singleton
    if isinstance(region, sublime.Region):
        region = [region]

    # Split the region up, so that each region returned exists on exactly one line
    region_split = []
    for region_part in region:
        region_split.extend(view.split_by_newlines(region_part))

    # Get row (line) number for each region area
    for region_area in region_split:
        # Retrieve line region for current region area
        row_line = view.line(region_area)
        # Check if line region is empty
        if filter_empty and row_line.empty():
            continue
        # Get beginning coordination point of line region
        row_point = row_line.begin()
        # Retrieve row (line) number and column number of region
        row, col = view.rowcol(row_point)
        # Convert from 0 based to a 1 based row (line) number
        row_number = str(row + 1)
        # Add to list for result
        rows.append(row_number)

    return rows


def render_regions(view=None):
    """
    Set breakpoint/current line marker(s) for current active view.
    """
    # Get current active view
    if view is None:
        view = sublime.active_window().active_view()

    # Remove all markers to avoid marker conflict
    view.erase_regions(S.REGION_KEY_BREAKPOINT)
    view.erase_regions(S.REGION_KEY_CURRENT)

    # Get filename of current view and check if is a valid filename
    filename = view.file_name()
    if not filename:
        return

    # Get all breakpoint rows (line numbers) for file
    breakpoint_rows = {}
    if filename in S.BREAKPOINT:
        breakpoint_rows = H.dictionary_keys(S.BREAKPOINT[filename])

    # Get current line from breakpoint hit
    if S.BREAKPOINT_ROW is not None:
        # Make sure current breakpoint is in this file
        if filename == S.BREAKPOINT_ROW['filename']:
            icon = S.ICON_CURRENT
            # Remove current line number from breakpoint rows to avoid marker conflict
            if S.BREAKPOINT_ROW['lineno'] in breakpoint_rows:
                icon = S.ICON_BREAKPOINT_CURRENT
                breakpoint_rows.remove(S.BREAKPOINT_ROW['lineno'])
            # Set current line marker
            view.add_regions(S.REGION_KEY_CURRENT, rows_to_region(S.BREAKPOINT_ROW['lineno']), S.REGION_SCOPE_CURRENT, icon, sublime.HIDDEN)

    # Set breakpoint marker(s)
    if breakpoint_rows:
        view.add_regions(S.REGION_KEY_BREAKPOINT, rows_to_region(breakpoint_rows), S.REGION_SCOPE_BREAKPOINT, S.ICON_BREAKPOINT, sublime.HIDDEN)