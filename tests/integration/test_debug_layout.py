try:
    from xdebug.unittesting import XdebugDeferrableTestCase
except:
    from SublimeTextXdebug.xdebug.unittesting import XdebugDeferrableTestCase


class TestDebugLayout(XdebugDeferrableTestCase):

    def window_does_not_have_debug_layout(self):
        breakpoint_view = self.get_view_by_title('Xdebug Breakpoint')
        context_view = self.get_view_by_title('Xdebug Context')
        stack_view = self.get_view_by_title('Xdebug Stack')
        watch_view = self.get_view_by_title('Xdebug Watch')
        return not breakpoint_view and not context_view and not stack_view and not watch_view

    def test_debug_layout_remains_open_on_session_stop(self):
        self.set_xdebug_settings({
            'break_on_start': True
        })
        yield self.window_has_xdebug_settings

        self.run_command('xdebug_session_start')
        yield self.window_has_debug_layout

        stack_view = self.get_view_by_title('Xdebug Stack')
        self.send_server_request()

        def stack_has_content():
            return not self.view_is_empty(stack_view)
        yield stack_has_content

        self.run_command('xdebug_session_stop')

        self.assertIsNotNone(self.get_view_by_title('Xdebug Breakpoint'))
        self.assertIsNotNone(self.get_view_by_title('Xdebug Context'))
        self.assertIsNotNone(self.get_view_by_title('Xdebug Stack'))
        self.assertIsNotNone(self.get_view_by_title('Xdebug Watch'))

    def test_debug_layout_is_restored_after_session_stop(self):
        self.set_xdebug_settings({
            'break_on_start': True
        })
        yield self.window_has_xdebug_settings

        self.run_command('xdebug_session_start')
        yield self.window_has_debug_layout

        stack_view = self.get_view_by_title('Xdebug Stack')
        self.send_server_request()

        def stack_has_content():
            return not self.view_is_empty(stack_view)
        yield stack_has_content

        self.run_command('xdebug_session_stop')

        self.assertIsNotNone(self.get_view_by_title('Xdebug Breakpoint'))
        self.assertIsNotNone(self.get_view_by_title('Xdebug Context'))
        self.assertIsNotNone(self.get_view_by_title('Xdebug Stack'))
        self.assertIsNotNone(self.get_view_by_title('Xdebug Watch'))

        self.run_command('xdebug_layout', {'restore': True})
        yield self.window_does_not_have_debug_layout

        self.assertIsNone(self.get_view_by_title('Xdebug Breakpoint'))
        self.assertIsNone(self.get_view_by_title('Xdebug Context'))
        self.assertIsNone(self.get_view_by_title('Xdebug Stack'))
        self.assertIsNone(self.get_view_by_title('Xdebug Watch'))

    def test_debug_layout_is_closed_on_session_stop(self):
        self.set_xdebug_settings({
            'break_on_start': True,
            'close_on_stop': True
        })
        yield self.window_has_xdebug_settings

        self.run_command('xdebug_session_start')
        yield self.window_has_debug_layout

        stack_view = self.get_view_by_title('Xdebug Stack')
        self.send_server_request()

        def stack_has_content():
            return not self.view_is_empty(stack_view)
        yield stack_has_content

        self.run_command('xdebug_session_stop')
        yield self.window_does_not_have_debug_layout

        self.assertIsNone(self.get_view_by_title('Xdebug Breakpoint'))
        self.assertIsNone(self.get_view_by_title('Xdebug Context'))
        self.assertIsNone(self.get_view_by_title('Xdebug Stack'))
        self.assertIsNone(self.get_view_by_title('Xdebug Watch'))
