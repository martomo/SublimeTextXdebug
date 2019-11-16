import re
import sys

# Helper module
try:
    from .helper import H
except:
    from helper import H

# HTML entities
try:
    from html.entities import name2codepoint
except ImportError:
    from htmlentitydefs import name2codepoint

# XML parser
try:
    from xml.etree import cElementTree as ET
except ImportError:
    try:
        from xml.etree import ElementTree as ET
    except ImportError:
        from .elementtree import ElementTree as ET
try:
    from xml.parsers import expat  # noqa: F401
    UNESCAPE_RESPONSE_DATA = True
except ImportError:
    # Module xml.parsers.expat missing, using SimpleXMLTreeBuilder
    from .elementtree import SimpleXMLTreeBuilder
    ET.XMLTreeBuilder = SimpleXMLTreeBuilder.TreeBuilder
    UNESCAPE_RESPONSE_DATA = False


ILLEGAL_XML_UNICODE_CHARACTERS = [
    (0x00, 0x08), (0x0B, 0x0C), (0x0E, 0x1F), (0x7F, 0x84),
    (0x86, 0x9F), (0xD800, 0xDFFF), (0xFDD0, 0xFDDF),
    (0xFFFE, 0xFFFF),
    (0x1FFFE, 0x1FFFF), (0x2FFFE, 0x2FFFF), (0x3FFFE, 0x3FFFF),
    (0x4FFFE, 0x4FFFF), (0x5FFFE, 0x5FFFF), (0x6FFFE, 0x6FFFF),
    (0x7FFFE, 0x7FFFF), (0x8FFFE, 0x8FFFF), (0x9FFFE, 0x9FFFF),
    (0xAFFFE, 0xAFFFF), (0xBFFFE, 0xBFFFF), (0xCFFFE, 0xCFFFF),
    (0xDFFFE, 0xDFFFF), (0xEFFFE, 0xEFFFF), (0xFFFFE, 0xFFFFF),
    (0x10FFFE, 0x10FFFF)]

ILLEGAL_XML_RANGES = [
    '%s-%s' % (H.unicode_chr(low), H.unicode_chr(high))
    for (low, high) in ILLEGAL_XML_UNICODE_CHARACTERS
    if low < sys.maxunicode
]

ILLEGAL_XML_RE = re.compile(H.unicode_string('[%s]') % H.unicode_string('').join(ILLEGAL_XML_RANGES))


def __convert(matches):
    text = matches.group(0)
    # Character reference
    if text[:2] == '&#':
        try:
            if text[:3] == '&#x':
                return H.unicode_chr(int(text[3:-1], 16))
            else:
                return H.unicode_chr(int(text[2:-1]))
        except ValueError:
            pass
    # Named entity
    else:
        try:
            # Following are not needed to be converted for XML
            if text[1:-1] in ('amp', 'apos', 'gt', 'lt', 'quot'):
                pass
            else:
                text = H.unicode_chr(name2codepoint[text[1:-1]])
        except KeyError:
            pass
    return text


def __unescape(string):
    """
    Convert HTML entities and character references to ordinary characters.
    """
    return re.sub(r'&#?\w+;', __convert, string)


def fromstring(data):

    # Remove special character quoting
    if UNESCAPE_RESPONSE_DATA:
        data = __unescape(data)

    # Replace invalid XML characters
    data = ILLEGAL_XML_RE.sub('?', data)

    # Create XML document object
    document = ET.fromstring(data)
    return document
