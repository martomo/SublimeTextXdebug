import os
try:
    from xdebug.unittesting import XdebugDeferrableTestCase
except:
    from SublimeTextXdebug.xdebug.unittesting import XdebugDeferrableTestCase


class TestBreakpointException(XdebugDeferrableTestCase):
    breakpoint_exception_file = 'breakpoint_exception.php'
    breakpoint_exception_file_local_path = os.path.join(XdebugDeferrableTestCase.local_path, breakpoint_exception_file)

    def test_break_on_deprecated(self):
        self.run_command('xdebug_session_start')
        yield self.window_has_debug_layout

        breakpoint_view = self.get_view_by_title('Xdebug Breakpoint')
        context_view = self.get_view_by_title('Xdebug Context')
        stack_view = self.get_view_by_title('Xdebug Stack')

        self.assertViewIsEmpty(breakpoint_view)
        self.assertViewIsEmpty(context_view)
        self.assertViewIsEmpty(stack_view)

        self.send_server_request(path=self.breakpoint_exception_file, params={'exception': 'Deprecated'})

        def stack_has_content():
            return not self.view_is_empty(stack_view)
        yield stack_has_content

        self.assertViewContains(stack_view, '[Deprecated] Non-static method Deprecated::get() should not be called statically')
        self.assertViewContains(stack_view, '[0] file://{remote_path}/{file}:16, {{main}}()'.format(remote_path=self.remote_path, file=self.breakpoint_exception_file))

    def test_break_on_fatal_error(self):
        self.run_command('xdebug_session_start')
        yield self.window_has_debug_layout

        breakpoint_view = self.get_view_by_title('Xdebug Breakpoint')
        context_view = self.get_view_by_title('Xdebug Context')
        stack_view = self.get_view_by_title('Xdebug Stack')

        self.assertViewIsEmpty(breakpoint_view)
        self.assertViewIsEmpty(context_view)
        self.assertViewIsEmpty(stack_view)

        self.send_server_request(path=self.breakpoint_exception_file, params={'exception': 'Fatal error'})

        def stack_has_content():
            return not self.view_is_empty(stack_view)
        yield stack_has_content

        self.assertViewContains(stack_view, "[Fatal error] Uncaught Exception: I'm sorry Dave, I'm afraid I can't do that. in {remote_path}/{file}:28".format(remote_path=self.remote_path, file=self.breakpoint_exception_file))
        self.assertViewContains(stack_view, '[0] file://{remote_path}/{file}:28, {{unknown}}()'.format(remote_path=self.remote_path, file=self.breakpoint_exception_file))

    def test_break_on_notice(self):
        self.run_command('xdebug_session_start')
        yield self.window_has_debug_layout

        breakpoint_view = self.get_view_by_title('Xdebug Breakpoint')
        context_view = self.get_view_by_title('Xdebug Context')
        stack_view = self.get_view_by_title('Xdebug Stack')

        self.assertViewIsEmpty(breakpoint_view)
        self.assertViewIsEmpty(context_view)
        self.assertViewIsEmpty(stack_view)

        self.send_server_request(path=self.breakpoint_exception_file, params={'exception': 'Notice'})

        def stack_has_content():
            return not self.view_is_empty(stack_view)
        yield stack_has_content

        self.assertViewContains(stack_view, '[Notice] Undefined variable: notice')
        self.assertViewContains(stack_view, '[0] file://{remote_path}/{file}:19, {{main}}()'.format(remote_path=self.remote_path, file=self.breakpoint_exception_file))

    def test_break_on_parse_error(self):
        self.run_command('xdebug_session_start')
        yield self.window_has_debug_layout

        breakpoint_view = self.get_view_by_title('Xdebug Breakpoint')
        context_view = self.get_view_by_title('Xdebug Context')
        stack_view = self.get_view_by_title('Xdebug Stack')

        self.assertViewIsEmpty(breakpoint_view)
        self.assertViewIsEmpty(context_view)
        self.assertViewIsEmpty(stack_view)

        self.send_server_request(path=self.breakpoint_exception_file, params={'exception': 'Parse error'})

        def stack_has_content():
            return not self.view_is_empty(stack_view)
        yield stack_has_content

        self.assertViewContains(stack_view, '[Parse error] syntax error, unexpected end of file')
        self.assertViewContains(stack_view, '[0] file://{remote_path}/{file}:4, {{unknown}}()'.format(remote_path=self.remote_path, file='breakpoint_exception_parse_error.php'))

    def test_break_on_warning(self):
        self.run_command('xdebug_session_start')
        yield self.window_has_debug_layout

        breakpoint_view = self.get_view_by_title('Xdebug Breakpoint')
        context_view = self.get_view_by_title('Xdebug Context')
        stack_view = self.get_view_by_title('Xdebug Stack')

        self.assertViewIsEmpty(breakpoint_view)
        self.assertViewIsEmpty(context_view)
        self.assertViewIsEmpty(stack_view)

        self.send_server_request(path=self.breakpoint_exception_file, params={'exception': 'Warning'})

        def stack_has_content():
            return not self.view_is_empty(stack_view)
        yield stack_has_content

        self.assertViewContains(stack_view, '[Warning] include(breakpoint_exception_warning.php): failed to open stream: No such file or directory')
        self.assertViewContains(stack_view, '[0] file://{remote_path}/{file}:25, {{main}}()'.format(remote_path=self.remote_path, file=self.breakpoint_exception_file))
