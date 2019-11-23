import os
try:
    from xdebug.unittesting import XdebugDeferrableTestCase
except:
    from SublimeTextXdebug.xdebug.unittesting import XdebugDeferrableTestCase


class TestBreakpointStep(XdebugDeferrableTestCase):
    breakpoint_step_file = 'breakpoint_step.php'
    breakpoint_step_file_local_path = os.path.join(XdebugDeferrableTestCase.local_path, breakpoint_step_file)

    def test_step_into(self):
        self.set_breakpoint(self.breakpoint_step_file_local_path, 11)

        self.run_command('xdebug_session_start')
        yield self.window_has_debug_layout

        breakpoint_view = self.get_view_by_title('Xdebug Breakpoint')
        context_view = self.get_view_by_title('Xdebug Context')
        stack_view = self.get_view_by_title('Xdebug Stack')

        self.assertViewContains(breakpoint_view, '=> {file_local_path}\n\t|+| 11'.format(file_local_path=self.breakpoint_step_file_local_path))
        self.assertViewIsEmpty(context_view)
        self.assertViewIsEmpty(stack_view)

        self.send_server_request(path=self.breakpoint_step_file)

        def context_and_stack_have_content():
            return not self.view_is_empty(context_view) and not self.view_is_empty(stack_view)
        yield context_and_stack_have_content

        self.assertViewContains(context_view, '$greeting = <uninitialized>')
        self.assertViewContains(stack_view, '[0] file://{remote_path}/{file}:11, {{main}}()'.format(remote_path=self.remote_path, file=self.breakpoint_step_file))

        context_view_contents = self.get_contents_of_view(context_view)
        stack_view_contents = self.get_contents_of_view(stack_view)

        def context_and_stack_have_different_content():
            return self.get_contents_of_view(context_view) != context_view_contents and self.get_contents_of_view(stack_view) != stack_view_contents

        self.run_command('xdebug_execute', {'command': 'step_into'})
        yield context_and_stack_have_different_content
        yield context_and_stack_have_content

        self.assertViewContains(context_view, '$greet = <uninitialized>')
        self.assertViewContains(context_view, '$name = (string) Stranger')
        self.assertViewContains(stack_view, '[0] file://{remote_path}/{file}:4, greet()'.format(remote_path=self.remote_path, file=self.breakpoint_step_file))

        context_view_contents = self.get_contents_of_view(context_view)
        stack_view_contents = self.get_contents_of_view(stack_view)

        def context_and_stack_have_different_content():
            return self.get_contents_of_view(context_view) != context_view_contents and self.get_contents_of_view(stack_view) != stack_view_contents

        self.run_command('xdebug_execute', {'command': 'step_into'})
        yield context_and_stack_have_different_content
        yield context_and_stack_have_content

        self.assertViewContains(context_view, '$greet = (string) Hi')
        self.assertViewContains(context_view, '$name = (string) Stranger')
        self.assertViewContains(stack_view, '[0] file://{remote_path}/{file}:5, greet()'.format(remote_path=self.remote_path, file=self.breakpoint_step_file))

    def test_step_out(self):
        self.set_breakpoint(self.breakpoint_step_file_local_path, 5)

        self.run_command('xdebug_session_start')
        yield self.window_has_debug_layout

        breakpoint_view = self.get_view_by_title('Xdebug Breakpoint')
        context_view = self.get_view_by_title('Xdebug Context')
        stack_view = self.get_view_by_title('Xdebug Stack')

        self.assertViewContains(breakpoint_view, '=> {file_local_path}\n\t|+| 5'.format(file_local_path=self.breakpoint_step_file_local_path))
        self.assertViewIsEmpty(context_view)
        self.assertViewIsEmpty(stack_view)

        self.send_server_request(path=self.breakpoint_step_file)

        def context_and_stack_have_content():
            return not self.view_is_empty(context_view) and not self.view_is_empty(stack_view)
        yield context_and_stack_have_content

        self.assertViewContains(context_view, '$greet = (string) Hi')
        self.assertViewContains(context_view, '$name = (string) Stranger')
        self.assertViewContains(stack_view, '[0] file://{remote_path}/{file}:5, greet()'.format(remote_path=self.remote_path, file=self.breakpoint_step_file))

        context_view_contents = self.get_contents_of_view(context_view)
        stack_view_contents = self.get_contents_of_view(stack_view)

        def context_and_stack_have_different_content():
            return self.get_contents_of_view(context_view) != context_view_contents and self.get_contents_of_view(stack_view) != stack_view_contents

        self.run_command('xdebug_execute', {'command': 'step_out'})
        yield context_and_stack_have_different_content
        yield context_and_stack_have_content

        self.assertViewContains(context_view, '$greeting = (string) Hello Stranger!')
        self.assertViewContains(stack_view, '[0] file://{remote_path}/{file}:12, {{main}}()'.format(remote_path=self.remote_path, file=self.breakpoint_step_file))

    def test_step_over(self):
        self.set_breakpoint(self.breakpoint_step_file_local_path, 11)

        self.run_command('xdebug_session_start')
        yield self.window_has_debug_layout

        breakpoint_view = self.get_view_by_title('Xdebug Breakpoint')
        context_view = self.get_view_by_title('Xdebug Context')
        stack_view = self.get_view_by_title('Xdebug Stack')

        self.assertViewContains(breakpoint_view, '=> {file_local_path}\n\t|+| 11'.format(file_local_path=self.breakpoint_step_file_local_path))
        self.assertViewIsEmpty(context_view)
        self.assertViewIsEmpty(stack_view)

        self.send_server_request(path=self.breakpoint_step_file)

        def context_and_stack_have_content():
            return not self.view_is_empty(context_view) and not self.view_is_empty(stack_view)
        yield context_and_stack_have_content

        self.assertViewContains(context_view, '$greeting = <uninitialized>')
        self.assertViewContains(stack_view, '[0] file://{remote_path}/{file}:11, {{main}}()'.format(remote_path=self.remote_path, file=self.breakpoint_step_file))

        context_view_contents = self.get_contents_of_view(context_view)
        stack_view_contents = self.get_contents_of_view(stack_view)

        def context_and_stack_have_different_content():
            return self.get_contents_of_view(context_view) != context_view_contents and self.get_contents_of_view(stack_view) != stack_view_contents

        self.run_command('xdebug_execute', {'command': 'step_over'})
        yield context_and_stack_have_different_content
        yield context_and_stack_have_content

        self.assertViewContains(context_view, '$greeting = (string) Hello Stranger!')
        self.assertViewContains(stack_view, '[0] file://{remote_path}/{file}:12, {{main}}()'.format(remote_path=self.remote_path, file=self.breakpoint_step_file))
