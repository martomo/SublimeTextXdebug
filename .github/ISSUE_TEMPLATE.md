<!--
Before submitting a new issue, please ensure to:
- Check the Troubleshoot section in README.md (https://github.com/martomo/SublimeTextXdebug#troubleshoot)
- Search for existing issues (https://github.com/martomo/SublimeTextXdebug/issues)
- Cleanup extraneous template details
-->

Provide here a description of the bug or feature request.
More details the better, such as reproduction steps for a bug if possible.
Please also try to fill in the following details when reporting a bug:

## Environment

### Sublime Text
__Operating system:__
<!-- On which version of Windows, Linux or macOS are you running Sublime Text -->
__Installed version/build:__
<!-- See "About Sublime Text" for version and build number -->
__Python version:__
<!-- Result of executing `import sys; print(sys.version)` in Console -->

### Server
__Operating system:__
<!--
Are you trying to debug the script remotely or locally?
In case operating system differs from Sublime Text, what distribution (Windows/Unix) is your server running?
-->
__PHP/Xdebug version:__
<!--
Determine the PHP/Xdebug version by either running `php -v` through command line or opening .php file in browser using `phpinfo()` function, depending on how it is intended to debug the script, through browser or command line operation.
-->

## Configuration

__php.ini/xdebug.ini__
<!-- See https://github.com/martomo/SublimeTextXdebug#xdebug -->
```ini
[xdebug]
# ...
```

__Packages/User/Xdebug.sublime-settings__
<!-- See https://github.com/martomo/SublimeTextXdebug#configuration -->
```json
{

}
```
__*.sublime-project__
<!-- In case of no project settings this section can be removed -->
```json
{

}
```

## Logs

__Console output:__
<!--
Include any additional information shown in Console if available.
Open Console through menu "View / Show Console", or "CTRL+`" shortcut.
-->
```

```
__Packages/User/Xdebug.log:__
<!-- If possible include contents of log file with 'debug' configuration set to 'True' -->
```

```
