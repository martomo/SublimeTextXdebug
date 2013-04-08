import sublime

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
        # TODO: Python 2.* support for checking string is digit
        if isinstance(row, int) or (isinstance(row, str) and row.isdigit()):
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


def update_regions():
    """
    Set breakpoint/current line marker(s) for current active view.
    """
    # Get current active view
    view = sublime.active_window().active_view()

    # Filename of current view
    filename = view.file_name()

    # Remove all markers if file has no breakpoints
    if filename not in S.BREAKPOINT or not S.BREAKPOINT[filename]:
        view.erase_regions(S.REGION_KEY_BREAKPOINT)
        view.erase_regions(S.REGION_KEY_CURRENT)
        return

    # Get all breakpoint rows (line numbers) for file
    breakpoint_rows = H.dictionary_keys(S.BREAKPOINT[filename])

    # Get current line from breakpoint hit
    remove_current = True
    if S.BREAKPOINT_ROW is not None:
        # Make sure current breakpoint is in this file
        if filename == S.BREAKPOINT_ROW['filename']:
            icon = S.ICON_CURRENT
            # Remove current line number from breakpoint rows to avoid marker conflict
            if S.BREAKPOINT_ROW['lineno'] in breakpoint_rows:
                icon = S.ICON_BREAKPOINT_CURRENT
                breakpoint_rows.remove(S.BREAKPOINT_ROW['lineno'])
            # Set current line marker
            remove_current = False
            view.add_regions(S.REGION_KEY_CURRENT, rows_to_region(S.BREAKPOINT_ROW['lineno']), S.REGION_SCOPE_CURRENT, icon, sublime.HIDDEN)

    # When no current line marker is set, make sure it is removed
    if remove_current:
        view.erase_regions(S.REGION_KEY_CURRENT)

    # Set breakpoint marker(s)
    view.add_regions(S.REGION_KEY_BREAKPOINT, rows_to_region(breakpoint_rows), S.REGION_SCOPE_BREAKPOINT, S.ICON_BREAKPOINT, sublime.HIDDEN)