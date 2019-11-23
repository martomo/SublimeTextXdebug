import unittest

from xdebug.xmlparser import fromstring


class TestXmlparser(unittest.TestCase):

    def test_response(self):
        xml = fromstring('<response xmlns="urn:debugger_protocol_v1" xmlns:xdebug="http://xdebug.org/dbgp/xdebug" command="feature_set" transaction_id="1" feature="show_hidden" success="1"></response>')
        self.assertEqual(xml.get('command'), 'feature_set')
