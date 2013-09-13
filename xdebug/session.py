import sublime

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

# DBGp protocol constants
try:
    from . import dbgp
except:
    import dbgp

# Log module
from .log import debug, info

# Protocol module
from .protocol import ProtocolConnectionException


def is_connected(show_status=False):
    """
    Check if client is connected to debugger engine.

    Keyword arguments:
    show_status -- Show message why client is not connected in status bar.
    """
    if S.SESSION and S.SESSION.connected:
        return True
    elif S.SESSION and show_status:
        sublime.status_message('Xdebug: Waiting for response from debugger engine.')
    elif show_status:
        sublime.status_message('Xdebug: No Xdebug session running.')
    return False


def connection_error(message):
    """
    Template for showing error message on connection error/loss.

    Keyword arguments:
    message -- Exception/reason of connection error/loss.
    """
    sublime.error_message("Please restart Xdebug debugging session.\nDisconnected from Xdebug debugger engine.\n" + message)
    info("Connection lost with debugger engine.")
    debug(message)
    # Reset connection
    try:
        S.SESSION.clear()
    except:
        pass
    finally:
        S.SESSION = None
        S.BREAKPOINT_ROW = None
        S.CONTEXT_DATA.clear()


def get_breakpoint_values():
    """
    Get list of all configured breakpoints.
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


def get_context_values():
    """
    Get variables in current context.
    """
    if S.SESSION:
        context = H.new_dictionary()
        try:
            # Super global variables
            if S.get_config_value('super_globals'):
                S.SESSION.send(dbgp.CONTEXT_GET, c=1)
                response = S.SESSION.read()
                context.update(get_response_properties(response))

            # Local variables
            S.SESSION.send(dbgp.CONTEXT_GET)
            response = S.SESSION.read()
            context.update(get_response_properties(response))
        except ProtocolConnectionException:
            e = sys.exc_info()[1]
            connection_error("%s" % e)

        # Store context variables in session
        S.CONTEXT_DATA = context

        return generate_context_output(context)


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
            property_value = None
            if child.text:
                try:
                    # Try to base64 decode value
                    property_value = H.base64_decode(child.text)
                except:
                    # Return raw value
                    property_value = child.text

            if property_name is not None and len(property_name) > 0:
                property_key = property_name
                # Ignore following properties
                if property_name == "::":
                    continue

                # Avoid nasty static functions/variables from turning in an infinitive loop
                if property_name.count("::") > 1:
                    continue

                # Filter password values
                if S.get_config_value('hide_password', True) and property_name.lower().find('password') != -1 and property_value is not None:
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


def get_stack_values():
    """
    Get stack information for current context.
    """
    values = H.unicode_string('')
    if S.SESSION:
        try:
            # Get stack information
            S.SESSION.send(dbgp.STACK_GET)
            response = S.SESSION.read()

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
        except ProtocolConnectionException:
            e = sys.exc_info()[1]
            connection_error("%s" % e)
    return values


def get_watch_values():
    """
    Get list of all watch expressions.
    """
    for index, item in enumerate(S.WATCH):
        # Reset value for watch expression
        S.WATCH[index]['value'] = None
        # Evaluate watch expression when connected to debugger engine
        if is_connected():
            try:
                if item['enabled']:
                    S.WATCH[index]['value'] = eval_watch_expression(item['expression'])
            except:
                pass
    return generate_watch_output(S.WATCH)


def eval_watch_expression(expression):
    if S.SESSION:
        try:
            S.SESSION.send(dbgp.EVAL, expression=expression)
            response = S.SESSION.read()

            return get_response_properties(response, expression)
        except ProtocolConnectionException:
            pass

    return None


def generate_watch_output(watch, indent=0):
    values = H.unicode_string('')
    if not isinstance(watch, list):
        return values
    for watch_data in watch:
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