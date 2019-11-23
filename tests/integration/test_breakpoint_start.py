import os
try:
    from xdebug.unittesting import XdebugDeferrableTestCase
except:
    from SublimeTextXdebug.xdebug.unittesting import XdebugDeferrableTestCase


class TestBreakpointStart(XdebugDeferrableTestCase):
    breakpoint_start_file = 'breakpoint_start.php'
    breakpoint_start_file_local_path = os.path.join(XdebugDeferrableTestCase.local_path, breakpoint_start_file)

    def test_break_on_start(self):
        self.set_xdebug_settings({
            'break_on_start': True
        })
        yield self.window_has_xdebug_settings

        self.run_command('xdebug_session_start')
        yield self.window_has_debug_layout

        breakpoint_view = self.get_view_by_title('Xdebug Breakpoint')
        context_view = self.get_view_by_title('Xdebug Context')
        stack_view = self.get_view_by_title('Xdebug Stack')

        self.assertViewIsEmpty(breakpoint_view)
        self.assertViewIsEmpty(context_view)
        self.assertViewIsEmpty(stack_view)

        self.send_server_request(path=self.breakpoint_start_file)

        def stack_has_content():
            return not self.view_is_empty(stack_view)
        yield stack_has_content

        self.assertViewContains(stack_view, '[0] file://{remote_path}/{file}.{{main}}:1'.format(remote_path=self.remote_path, file=self.breakpoint_start_file))

    def test_set_breakpoint(self):
        self.set_breakpoint(self.breakpoint_start_file_local_path, 3)

        self.run_command('xdebug_session_start')
        yield self.window_has_debug_layout

        breakpoint_view = self.get_view_by_title('Xdebug Breakpoint')
        context_view = self.get_view_by_title('Xdebug Context')
        stack_view = self.get_view_by_title('Xdebug Stack')

        self.assertViewContains(breakpoint_view, '=> {file_local_path}\n\t|+| 3'.format(file_local_path=self.breakpoint_start_file_local_path))
        self.assertViewIsEmpty(context_view)
        self.assertViewIsEmpty(stack_view)

        self.send_server_request(path=self.breakpoint_start_file)

        def context_and_stack_have_content():
            return not self.view_is_empty(context_view) and not self.view_is_empty(stack_view)
        yield context_and_stack_have_content

        self.assertViewContains(context_view, '$hello = <uninitialized>')
        self.assertViewContains(stack_view, '[0] file://{remote_path}/{file}:3, {{main}}()'.format(remote_path=self.remote_path, file=self.breakpoint_start_file))
