import sublime

import operator
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

# DBGp protocol constants
try:
    from . import dbgp
except:
    import dbgp

# Config module
from .config import get_value, get_window_value, set_window_value

# Util module
from .util import get_real_path, get_region_icon, save_watch_data


DATA_BREAKPOINT = 'breakpoint'
DATA_CONTEXT = 'context'
DATA_STACK = 'stack'
DATA_WATCH = 'watch'

TITLE_WINDOW_BREAKPOINT = "Xdebug Breakpoint"
TITLE_WINDOW_CONTEXT = "Xdebug Context"
TITLE_WINDOW_STACK = "Xdebug Stack"
TITLE_WINDOW_WATCH = "Xdebug Watch"


def close_debug_windows():
    """
    Close all debugging related views in active window.
    """
    window = sublime.active_window()
    for view in window.views():
        if is_debug_view(view):
            window.focus_view(view)
            window.run_command('close')
    window.run_command('hide_panel', {"panel": 'output.xdebug'})


def generate_breakpoint_output():
    """
    Generate output with all configured breakpoints.
    """
    # Get breakpoints for files
    values = H.unicode_string('')
    if S.BREAKPOINT is None:
        return values
    for filename, breakpoint_data in sorted(S.BREAKPOINT.items()):
        breakpoint_entry = ''
        if breakpoint_data:
            breakpoint_entry += "=> %s\n" % filename
            # Sort breakpoint data by line number
            for lineno, bp in sorted(breakpoint_data.items(), key=lambda item: (int(item[0]) if isinstance(item[0], int) or H.is_digit(item[0]) else float('inf'), item[0])):
                # Do not show temporary breakpoint
                if S.BREAKPOINT_RUN is not None and S.BREAKPOINT_RUN['filename'] == filename and S.BREAKPOINT_RUN['lineno'] == lineno:
                    continue
                # Whether breakpoint is enabled or disabled
                breakpoint_entry += '\t'
                if bp['enabled']:
                    breakpoint_entry += '|+|'
                else:
                    breakpoint_entry += '|-|'
                # Line number
                breakpoint_entry += ' %s' % lineno
                # Conditional expression
                if bp['expression'] is not None:
                    breakpoint_entry += ' -- "%s"' % bp['expression']
                breakpoint_entry += "\n"
        values += H.unicode_string(breakpoint_entry)
    return values


def generate_context_output(context, indent=0):
    """
    Generate readable context from dictionary with context data.

    Keyword arguments:
    context -- Dictionary with context data.
    indent -- Indent level.
    """
    # Generate output text for values
    values = H.unicode_string('')
    if not isinstance(context, dict):
        return values
    for variable in context.values():
        has_children = False
        property_text = ''
        # Set indentation
        for i in range(indent): property_text += '\t'
        # Property with value
        if variable['value'] is not None:
            if variable['name']:
                property_text += '{name} = '
            property_text += '({type}) {value}\n'
        # Property with children
        elif isinstance(variable['children'], dict) and variable['numchildren'] is not None:
            has_children = True
            if variable['name']:
                property_text += '{name} = '
            property_text += '{type}[{numchildren}]\n'
        # Unknown property
        else:
            if variable['name']:
                property_text += '{name} = '
            property_text += '<{type}>\n'

        # Remove newlines in value to prevent incorrect indentation
        value = ''
        if variable['value'] and len(variable['value']) > 0:
            value = variable['value'].replace("\r\n", "\n").replace("\n", " ")

        # Format string and append to output
        values += H.unicode_string(property_text \
                        .format(value=value, type=variable['type'], name=variable['name'], numchildren=variable['numchildren']))

        # Append property children to output
        if has_children:
            # Get children for property (no need to convert, already unicode)
            values += generate_context_output(variable['children'], indent+1)
            # Use ellipsis to indicate that results have been truncated
            limited = False
            if isinstance(variable['numchildren'], int) or H.is_digit(variable['numchildren']):
                if int(variable['numchildren']) != len(variable['children']):
                    limited = True
            elif len(variable['children']) > 0 and not variable['numchildren']:
                limited = True
            if limited:
                for i in range(indent+1): values += H.unicode_string('\t')
                values += H.unicode_string('...\n')
    return values


def generate_stack_output(response):
    values = H.unicode_string('')

    # Display exception name and message
    if S.BREAKPOINT_EXCEPTION:
        values += H.unicode_string('[{name}] {message}\n' \
                                  .format(name=S.BREAKPOINT_EXCEPTION['name'], message=S.BREAKPOINT_EXCEPTION['message']))

    # Walk through elements in response
    has_output = False
    try:
        for child in response:
            # Get stack attribute values
            if child.tag == dbgp.ELEMENT_STACK or child.tag == dbgp.ELEMENT_PATH_STACK:
                stack_level = child.get(dbgp.STACK_LEVEL, 0)
                stack_type = child.get(dbgp.STACK_TYPE)
                stack_file = H.url_decode(child.get(dbgp.STACK_FILENAME))
                stack_line = child.get(dbgp.STACK_LINENO, 0)
                stack_where = child.get(dbgp.STACK_WHERE, '{unknown}')
                # Append values
                values += H.unicode_string('[{level}] {filename}.{where}:{lineno}\n' \
                                          .format(level=stack_level, type=stack_type, where=stack_where, lineno=stack_line, filename=stack_file))
                has_output = True
    except:
        pass

    # When no stack use values from exception
    if not has_output and S.BREAKPOINT_EXCEPTION:
        values += H.unicode_string('[{level}] {filename}.{where}:{lineno}\n' \
                                  .format(level=0, where='{unknown}', lineno=S.BREAKPOINT_EXCEPTION['lineno'], filename=S.BREAKPOINT_EXCEPTION['filename']))

    return values


def generate_watch_output():
    """
    Generate output with all watch expressions.
    """
    values = H.unicode_string('')
    if S.WATCH is None:
        return values
    for watch_data in S.WATCH:
        watch_entry = ''
        if watch_data and isinstance(watch_data, dict):
            # Whether watch expression is enabled or disabled
            if 'enabled' in watch_data.keys():
                if watch_data['enabled']:
                    watch_entry += '|+|'
                else:
                    watch_entry += '|-|'
            # Watch expression
            if 'expression' in watch_data.keys():
                watch_entry += ' "%s"' % watch_data['expression']
            # Evaluated value
            if watch_data['value'] is not None:
                watch_entry += ' = ' + generate_context_output(watch_data['value'])
            else:
                watch_entry += "\n"
        values += H.unicode_string(watch_entry)
    return values


def get_context_variable(context, variable_name):
    """
    Find a variable in the context data.

    Keyword arguments:
    context -- Dictionary with context data to search.
    variable_name -- Name of variable to find.
    """
    if isinstance(context, dict):
        if variable_name in context:
            return context[variable_name]
        for variable in context.values():
            if isinstance(variable['children'], dict):
                children = get_context_variable(variable['children'], variable_name)
                if children:
                    return children


def get_debug_index(name=None):
    """
    Retrieve configured group/index position of of debug view(s) within active window.
    Returns list with tuple entries for all debug views or single tuple when specified name of debug view.
    Structure of tuple entry for debug view is as followed:
    (group position in window, index position in group, name/title of debug view)

    Keyword arguments:
    name -- Name of debug view to get group/index position.
    """
    # Set group and index for each debug view
    breakpoint_group = get_value(S.KEY_BREAKPOINT_GROUP, -1)
    breakpoint_index = get_value(S.KEY_BREAKPOINT_INDEX, 0)
    context_group = get_value(S.KEY_CONTEXT_GROUP, -1)
    context_index = get_value(S.KEY_CONTEXT_INDEX, 0)
    stack_group = get_value(S.KEY_STACK_GROUP, -1)
    stack_index = get_value(S.KEY_STACK_INDEX, 0)
    watch_group = get_value(S.KEY_WATCH_GROUP, -1)
    watch_index = get_value(S.KEY_WATCH_INDEX, 0)

    # Create list with all debug views and sort by group/index
    debug_list = []
    debug_list.append((breakpoint_group, breakpoint_index, TITLE_WINDOW_BREAKPOINT))
    debug_list.append((context_group, context_index, TITLE_WINDOW_CONTEXT))
    debug_list.append((stack_group, stack_index, TITLE_WINDOW_STACK))
    debug_list.append((watch_group, watch_index, TITLE_WINDOW_WATCH))
    debug_list.sort(key=operator.itemgetter(0,1))

    # Recalculate group/index position within boundaries of active window
    window = sublime.active_window()
    group_limit = window.num_groups()-1
    sorted_list = []
    last_group = None
    last_index = 0
    for debug in debug_list:
        group, index, title = debug
        # Set group position
        if group > group_limit:
            group = group_limit
        # Set index position
        if group == last_group:
            last_index += 1
        else:
            index_limit = len(window.views_in_group(group))
            if index > index_limit:
                index = index_limit
            last_group = group
            last_index = index
        # Add debug view with new group/index
        sorted_list.append((group, last_index, title))
    # Sort recalculated list by group/index
    sorted_list.sort(key=operator.itemgetter(0,1))

    # Find specified view by name/title of debug view
    if name is not None:
        try:
            return [view[2] for view in sorted_list].index(name)
        except ValueError:
            return None

    # List with all debug views
    return sorted_list


def get_response_properties(response, default_key=None):
    """
    Return a dictionary with available properties from response.

    Keyword arguments:
    response -- Response from debugger engine.
    default_key -- Index key to use when property has no name.
    """
    properties = H.new_dictionary()
    # Walk through elements in response
    for child in response:
        # Read property elements
        if child.tag == dbgp.ELEMENT_PROPERTY or child.tag == dbgp.ELEMENT_PATH_PROPERTY:
            # Get property attribute values
            property_name_short = child.get(dbgp.PROPERTY_NAME)
            property_name = child.get(dbgp.PROPERTY_FULLNAME, property_name_short)
            property_type = child.get(dbgp.PROPERTY_TYPE)
            property_children = child.get(dbgp.PROPERTY_CHILDREN)
            property_numchildren = child.get(dbgp.PROPERTY_NUMCHILDREN)
            property_classname = child.get(dbgp.PROPERTY_CLASSNAME)
            property_encoding = child.get(dbgp.PROPERTY_ENCODING)
            property_value = None

            # Set property value
            if child.text:
                property_value = child.text
                # Try to decode property value when encoded with base64
                if property_encoding is not None and property_encoding == 'base64':
                    try:
                        property_value = H.base64_decode(child.text)
                    except:
                        pass

            if property_name is not None and len(property_name) > 0:
                property_key = property_name
                # Ignore following properties
                if property_name == "::":
                    continue

                # Avoid nasty static functions/variables from turning in an infinitive loop
                if property_name.count("::") > 1:
                    continue

                # Filter password values
                if get_value(S.KEY_HIDE_PASSWORD, True) and property_name.lower().find('password') != -1 and property_value is not None:
                    property_value = '******'
            else:
                property_key = default_key

            # Store property
            if property_key:
                properties[property_key] = { 'name': property_name, 'type': property_type, 'value': property_value, 'numchildren': property_numchildren, 'children' : None }

                # Get values for children
                if property_children:
                    properties[property_key]['children'] = get_response_properties(child, default_key)

                # Set classname, if available, as type for object
                if property_classname and property_type == 'object':
                    properties[property_key]['type'] = property_classname
        # Handle error elements
        elif child.tag == dbgp.ELEMENT_ERROR or child.tag == dbgp.ELEMENT_PATH_ERROR:
            message = 'error'
            for step_child in child:
                if step_child.tag == dbgp.ELEMENT_MESSAGE or step_child.tag == dbgp.ELEMENT_PATH_MESSAGE and step_child.text:
                    message = step_child.text
                    break
            if default_key:
                properties[default_key] = { 'name': None, 'type': message, 'value': None, 'numchildren': None, 'children': None }
    return properties


def has_debug_view(name=None):
    """
    Determine if active window has any or specific debug view(s).

    Keyword arguments:
    name -- Name of debug view to search for in active window.
    """
    for view in sublime.active_window().views():
        if is_debug_view(view):
            if name is not None:
                if view.name() == name:
                    return True
            else:
                return True
    return False


def is_debug_view(view):
    """
    Check if view name matches debug name/title.

    Keyword arguments:
    view -- View reference which to check if name matches debug name/title.
    """
    return view.name() == TITLE_WINDOW_BREAKPOINT or view.name() == TITLE_WINDOW_CONTEXT or view.name() == TITLE_WINDOW_STACK or view.name() == TITLE_WINDOW_WATCH


def set_layout(layout):
    """
    Toggle between debug and default window layouts.
    """
    # Get active window and set reference to active view
    window = sublime.active_window()
    previous_active = window.active_view()

    # Do not set layout when disabled
    if get_value(S.KEY_DISABLE_LAYOUT):
        S.RESTORE_LAYOUT = window.get_layout()
        set_window_value('restore_layout', S.RESTORE_LAYOUT)
        S.RESTORE_INDEX = H.new_dictionary()
        set_window_value('restore_index', S.RESTORE_INDEX)
        return

    # Show debug layout
    if layout == 'debug':
        debug_layout = get_value(S.KEY_DEBUG_LAYOUT, S.LAYOUT_DEBUG)
        if window.get_layout() != debug_layout:
            # Save current layout
            S.RESTORE_LAYOUT = window.get_layout()
            set_window_value('restore_layout', S.RESTORE_LAYOUT)
            # Remember view indexes
            S.RESTORE_INDEX = H.new_dictionary()
            for view in window.views():
                view_id = "%d" % view.id()
                group, index = window.get_view_index(view)
                S.RESTORE_INDEX[view_id] = { "group": group, "index": index }
            set_window_value('restore_index', S.RESTORE_INDEX)
            # Set debug layout
            window.set_layout(S.LAYOUT_NORMAL)
        window.set_layout(debug_layout)
    # Show previous (single) layout
    else:
        # Get previous layout configuration
        if S.RESTORE_LAYOUT is None:
            S.RESTORE_LAYOUT = get_window_value('restore_layout', S.LAYOUT_NORMAL)
        if S.RESTORE_INDEX is None:
            S.RESTORE_INDEX = get_window_value('restore_index', {})
        # Restore layout
        window.set_layout(S.LAYOUT_NORMAL)
        window.set_layout(S.RESTORE_LAYOUT)
        for view in window.views():
            view_id = "%d" % view.id()
            # Set view indexes
            if view_id in H.dictionary_keys(S.RESTORE_INDEX):
                v = S.RESTORE_INDEX[view_id]
                window.set_view_index(view, v["group"], v["index"])

    # Restore focus to previous active view
    if not previous_active is None:
        window.focus_view(previous_active)


def show_content(data, content=None):
    """
    Show content for specific data type in assigned window view.
    Note: When view does not exists, it will create one.
    """

    # Hande data type
    if data == DATA_BREAKPOINT:
        title = TITLE_WINDOW_BREAKPOINT
        content = generate_breakpoint_output()
    elif data == DATA_CONTEXT:
        title = TITLE_WINDOW_CONTEXT
    elif data == DATA_STACK:
        title = TITLE_WINDOW_STACK
    elif data == DATA_WATCH:
        title = TITLE_WINDOW_WATCH
        content = generate_watch_output()
    else:
        return

    # Get list of group/index for all debug views
    debug_index = get_debug_index()

    # Find group/index of debug view for current data type
    try:
        key = [debug[2] for debug in debug_index].index(title)
    except ValueError:
        return
    # Set group and index position
    group, index, _ = debug_index[key]

    # Get active window and set reference to active view
    window = sublime.active_window()
    previous_active = window.active_view_in_group(window.active_group())

    # Loop through views in active window
    found = False
    view = None
    previous_key = -1
    active_debug = None
    for v in window.views():
        # Search for view assigned to data type
        if v.name() == title:
            found = True
            view = v
            continue
        # Adjust group/index of debug view depending on other debug view(s)
        if is_debug_view(v):
            try:
                current_key = [debug[2] for debug in debug_index].index(v.name())
            except ValueError:
                continue
            # Get current position of view
            view_group, view_index = window.get_view_index(v)
            # Recalculate group/index for debug view
            current_group, current_index, _ = debug_index[current_key]
            if group == current_group:
                if key > previous_key and key < current_key:
                    index = view_index
                if key > current_key:
                    index = view_index + 1
                    # Remember debug view for setting focus
                    if v == window.active_view_in_group(group):
                        active_debug = v
            previous_key = current_key

    # Make sure index position is not out of boundary
    index_limit = len(window.views_in_group(group))
    if index > index_limit:
        index = index_limit

    # Create new view if it does not exists
    if not found:
        view = window.new_file()
        view.set_scratch(True)
        view.set_read_only(True)
        view.set_name(title)
        window.set_view_index(view, group, index)
        # Set focus back to active debug view
        if active_debug is not None:
            window.focus_view(active_debug)

    # Strip .sublime-package of package name for syntax file
    package_extension = ".sublime-package"
    package = S.PACKAGE_FOLDER
    if package.endswith(package_extension):
        package = package[:-len(package_extension)]

    # Configure view settings
    view.settings().set('word_wrap', False)
    view.settings().set('syntax', 'Packages/' + package + '/Xdebug.tmLanguage')

    # Set content for view and fold all indendation blocks
    view.run_command('xdebug_view_update', {'data': content, 'readonly': True})
    if data == DATA_CONTEXT or data == DATA_WATCH:
        view.run_command('fold_all')

    # Restore focus to previous active view/group
    if previous_active is not None:
        window.focus_view(previous_active)
    else:
        window.focus_group(0)


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
            point = view.sel()[0]
            # Check if selected point uses variable scope
            if point.size() == 0 and sublime.score_selector(view.scope_name(point.a), 'variable'):
                # Find variable in line which contains the point
                line = view.substr(view.line(point))
                pattern = re.compile('^\\s*(\\$.*?)\\s+\\=')
                match = pattern.match(line)
                if match:
                    # Get variable details from context data
                    variable_name = match.group(1)
                    variable = get_context_variable(S.CONTEXT_DATA, variable_name)
                    if variable:
                        # Convert details to text output
                        variables = H.new_dictionary()
                        variables[variable_name] = variable
                        data = generate_context_output(variables)
                        # Show context variables and children in output panel
                        window = sublime.active_window()
                        panel = window.get_output_panel('xdebug')
                        panel.run_command("xdebug_view_update", {'data' : data} )
                        panel.run_command('set_setting', {"setting": 'word_wrap', "value": True})
                        window.run_command('show_panel', {"panel": 'output.xdebug'})
        except:
            pass


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


def show_panel_content(content):
    # Show response data in output panel
    try:
        window = sublime.active_window()
        panel = window.get_output_panel('xdebug')
        panel.run_command('xdebug_view_update', {'data': content})
        panel.run_command('set_setting', {"setting": 'word_wrap', "value": True})
        window.run_command('show_panel', {'panel': 'output.xdebug'})
    except:
        print(content)


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
    # Unable to convert rows to regions when no view available
    if view is None:
        return

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
    # Unable to convert regions to rows when no view available
    if view is None:
        return

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

    Note: View rendering conflict when using same icon for different scopes in add_regions().
    """
    # Get current active view
    if view is None:
        view = sublime.active_window().active_view()
    # Unable to set regions when no view available
    if view is None:
        return

    # Do no set regions if view is empty or still loading
    if view.size() == 0 or view.is_loading():
        return

    # Remove all markers to avoid marker conflict
    view.erase_regions(S.REGION_KEY_BREAKPOINT)
    view.erase_regions(S.REGION_KEY_CURRENT)
    view.erase_regions(S.REGION_KEY_DISABLED)

    # Get filename of current view and check if is a valid filename
    filename = view.file_name()
    if not filename:
        return

    # Determine icon for regions
    icon_current = get_region_icon(S.KEY_CURRENT_LINE)
    icon_disabled = get_region_icon(S.KEY_BREAKPOINT_DISABLED)
    icon_enabled = get_region_icon(S.KEY_BREAKPOINT_ENABLED)

    # Get all (disabled) breakpoint rows (line numbers) for file
    breakpoint_rows = []
    disabled_rows = []
    if filename in S.BREAKPOINT and isinstance(S.BREAKPOINT[filename], dict):
        for lineno, bp in S.BREAKPOINT[filename].items():
            # Do not show temporary breakpoint
            if S.BREAKPOINT_RUN is not None and S.BREAKPOINT_RUN['filename'] == filename and S.BREAKPOINT_RUN['lineno'] == lineno:
                continue
            # Determine if breakpoint is enabled or disabled
            if bp['enabled']:
                breakpoint_rows.append(lineno)
            else:
                disabled_rows.append(lineno)

    # Get current line from breakpoint hit
    if S.BREAKPOINT_ROW is not None:
        # Make sure current breakpoint is in this file
        if filename == S.BREAKPOINT_ROW['filename']:
            # Remove current line number from breakpoint rows to avoid marker conflict
            if S.BREAKPOINT_ROW['lineno'] in breakpoint_rows:
                breakpoint_rows.remove(S.BREAKPOINT_ROW['lineno'])
                # Set icon for current breakpoint
                icon_breakpoint_current = get_region_icon(S.KEY_BREAKPOINT_CURRENT)
                if icon_breakpoint_current:
                    icon_current = icon_breakpoint_current
            if S.BREAKPOINT_ROW['lineno'] in disabled_rows:
                disabled_rows.remove(S.BREAKPOINT_ROW['lineno'])
            # Set current line marker
            if icon_current:
                view.add_regions(S.REGION_KEY_CURRENT, rows_to_region(S.BREAKPOINT_ROW['lineno']), S.REGION_SCOPE_CURRENT, icon_current, sublime.HIDDEN)

    # Set breakpoint marker(s)
    if breakpoint_rows and icon_enabled:
        view.add_regions(S.REGION_KEY_BREAKPOINT, rows_to_region(breakpoint_rows), S.REGION_SCOPE_BREAKPOINT, icon_enabled, sublime.HIDDEN)
    if disabled_rows and icon_disabled:
        view.add_regions(S.REGION_KEY_DISABLED, rows_to_region(disabled_rows), S.REGION_SCOPE_BREAKPOINT, icon_disabled, sublime.HIDDEN)


def toggle_breakpoint(view):
    try:
        # Get selected point in view
        point = view.sel()[0]
        # Check if selected point uses breakpoint line scope
        if point.size() == 3 and sublime.score_selector(view.scope_name(point.a), 'xdebug.output.breakpoint.line'):
            # Find line number of breakpoint
            line = view.substr(view.line(point))
            pattern = re.compile('^\\s*(?:(\\|\\+\\|)|(\\|-\\|))\\s*(?P<line_number>\\d+)\\s*(?:(--)(.*)|.*)')
            match = pattern.match(line)
            # Check if it has found line number
            if match and match.group('line_number'):
                # Get all breakpoint filenames
                breakpoint_file = view.find_by_selector('xdebug.output.breakpoint.file')
                # Locate line with filename related to selected breakpoint
                file_line = None
                for entry in breakpoint_file:
                    # Stop searching if we have passed selected breakpoint
                    if entry > point:
                        break
                    file_line = view.substr(view.line(entry))
                # Do not continue without line containing filename
                if file_line is None:
                    return
                # Remove unnecessary text from line to get filename
                file_pattern = re.compile('^\\s*(=>)\\s*(?P<filename>.*)')
                file_match = file_pattern.match(file_line)
                # Check if it is a valid filename
                if file_match and file_match.group('filename'):
                    filename = file_match.group('filename')
                    line_number = match.group('line_number')
                    enabled = None
                    # Disable breakpoint
                    if sublime.score_selector(view.scope_name(point.a), 'entity') and S.BREAKPOINT[filename][line_number]['enabled']:
                        enabled = False
                    # Enable breakpoint
                    if sublime.score_selector(view.scope_name(point.a), 'keyword') and not S.BREAKPOINT[filename][line_number]['enabled']:
                        enabled = True
                    # Toggle breakpoint only if it has valid value
                    if enabled is None:
                        return
                    sublime.active_window().run_command('xdebug_breakpoint', {"enabled": enabled, "rows": [line_number], "filename": filename})
        # Check if selected point uses breakpoint file scope
        elif point.size() > 3 and sublime.score_selector(view.scope_name(point.a), 'xdebug.output.breakpoint.file'):
            # Get filename from selected line in view
            file_line = view.substr(view.line(point))
            file_pattern = re.compile('^\\s*(=>)\\s*(?P<filename>.*)')
            file_match = file_pattern.match(file_line)
            # Show file when it's a valid filename
            if file_match and file_match.group('filename'):
                filename = file_match.group('filename')
                show_file(filename)
    except:
        pass


def toggle_stack(view):
    try:
        # Get selected point in view
        point = view.sel()[0]
        # Check if selected point uses stack entry scope
        if point.size() > 3 and sublime.score_selector(view.scope_name(point.a), 'xdebug.output.stack.entry'):
            # Get fileuri and line number from selected line in view
            line = view.substr(view.line(point))
            pattern = re.compile('^(\[\d+\])\s*(?P<fileuri>.*)(\..*)(\s*:.*?(?P<lineno>\d+))\s*(\((.*?):.*\)|$)')
            match = pattern.match(line)
            # Show file when it's a valid fileuri
            if match and match.group('fileuri'):
                filename = get_real_path(match.group('fileuri'))
                lineno = 0
                if match.group('lineno'):
                    lineno = match.group('lineno')
                show_file(filename, lineno)
    except:
        pass


def toggle_watch(view):
    # Do not try to toggle when no watch expressions defined
    if not S.WATCH:
        return
    try:
        # Get selected point in view
        point = view.sel()[0]
        # Check if selected point uses watch entry scope
        if point.size() == 3 and sublime.score_selector(view.scope_name(point.a), 'xdebug.output.watch.entry'):
            # Determine if watch entry is enabled or disabled
            line = view.substr(view.line(point))
            pattern = re.compile('^(?:(?P<enabled>\\|\\+\\|)|(?P<disabled>\\|-\\|))\\.*')
            match = pattern.match(line)
            if match and (match.group('enabled') or match.group('disabled')):
                # Get all entries and determine index by line/point match
                watch = view.find_by_selector('xdebug.output.watch.entry')
                watch_index = 0
                for entry in watch:
                    # Stop searching if we have passed selected breakpoint
                    if entry > point:
                        break
                    # Only increment watch index when it contains expression
                    watch_line = view.substr(view.line(entry))
                    watch_match = pattern.match(watch_line)
                    if watch_match and (watch_match.group('enabled') or watch_match.group('disabled')):
                        watch_index += 1
                # Disable watch expression
                if sublime.score_selector(view.scope_name(point.a), 'entity') and S.WATCH[watch_index]['enabled']:
                    S.WATCH[watch_index]['enabled'] = False
                # Enable watch expression
                if sublime.score_selector(view.scope_name(point.a), 'keyword') and not S.WATCH[watch_index]['enabled']:
                    S.WATCH[watch_index]['enabled'] = True
                # Update watch view and save watch data to file
                sublime.active_window().run_command('xdebug_watch', {"update": True})
    except:
        pass