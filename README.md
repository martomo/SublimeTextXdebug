# SublimeTextXdebug
Xdebug debugger client integration for Sublime Text.

![SublimeTextXdebug](http://i.imgur.com/2FGYW3P.png)

Based on the Xdebug protocol functionality in [SublimeXdebug](https://github.com/Kindari/SublimeXdebug) package by [Kindari](https://github.com/Kindari).

## Overview
* [Features](#features)
* [Commands](#commands)
* [Installation](#installation)
* [Xdebug](#xdebug)
* [Configuration](#configuration)
* [Troubleshoot](#troubleshoot)
* [License](#license)

## Features
* Remote debugging by configuring path mapping
* Navigate on breakpoint hit to relevant file on specific line, when found on local drive
* Customizable debugging layout for displaying stack history and context variables with syntax
* Overview of breakpoints in all files and disable/enable breakpoints with simple click
* Evaluate code within the current execution context, by setting watch expressions
* Inspect (nested) context variables
* Works on both Sublime Text 2 __and__ 3

## Commands
Here is a complete list of commands you can find Command Pallette under the `Xdebug` namespace or in the menu under `Tools / Xdebug`:

#### Start/Stop debugging session
* Start Debugging - <kbd>Ctrl+Shift+F9</kbd> or <kbd>⌘+Shift+F9</kbd>
* Start Debugging (Launch Browser)
* Restart Session
* Stop Debugging - <kbd>Ctrl+Shift+F10</kbd> or <kbd>⌘+Shift+F10</kbd>
* Stop Debugging (Launch Browser)
* Stop Debugging (Close Windows)

*__Launch Browser__ menu option will only show if you have an url configured within [settings](#configuration).*

#### Breakpoints
* Add/Remove Breakpoint - <kbd>Ctrl+F8</kbd> or <kbd>⌘+F8</kbd>
* Set Conditional Breakpoint - <kbd>Shift+F8</kbd>
* Clear Breakpoints
* Clear All Breakpoints

#### Watch expressions
* Set Watch Expression
* Edit Watch Expression
* Remove Watch Expression
* Clear Watch Expressions

#### Session commands
* Evaluate
* Execute
* Status

#### Continuation commands
* Run - <kbd>Ctrl+Shift+F5</kbd> or <kbd>⌘+Shift+F5</kbd>
* Run To Line
* Step Over - <kbd>Ctrl+Shift+F6</kbd> or <kbd>⌘+Shift+F6</kbd>
* Step Into - <kbd>Ctrl+Shift+F7</kbd> or <kbd>⌘+Shift+F7</kbd>
* Step Out - <kbd>Ctrl+Shift+F8</kbd> or <kbd>⌘+Shift+F8</kbd>
* Stop
* Detach

#### Other
* Restore Layout / Close Windows - <kbd>Ctrl+Shift+F11</kbd> or <kbd>⌘+Shift+F11</kbd>
* Settings - Default
* Settings - User

## Installation

#### [Package Control](http://wbond.net/sublime_packages/package_control)
Execute __"Package Control: Install Package"__ in the Command Pallette to retrieve a list of available packages.
Search in the list and install package `Xdebug Client`.

#### Git
Clone the repository by executing the following command in your Packages directory:
```git clone https://github.com/martomo/SublimeTextXdebug.git "Xdebug Client"```

#### Download
Get the latest [source from GitHub](https://github.com/martomo/SublimeTextXdebug/archive/master.zip) and extract the source into your Packages directory.


*__Note:__ You can locate your Packages directory in the menu under* `Preferences / Browse Packages...`

## Xdebug
In order to be able to debug your PHP scripts, you will need have Xdebug extension installed on your server.
[See here for installation instructions](http://xdebug.org/docs/install)

Below is a configuration template for php.ini/xdebug.ini, be warned if you are on a Live environment, __remote_connect_back__ allows every debug request from any source to be accepted.

```ini
[xdebug]
zend_extension = /absolute/path/to/your/xdebug-extension.so
;zend_extension = "C:\Program Files (x86)\PHP\ext\php_xdebug.dll"
xdebug.remote_enable = 1
xdebug.remote_host = "127.0.0.1"
xdebug.remote_port = 9000
xdebug.remote_handler = "dbgp"
xdebug.remote_mode = req
xdebug.remote_connect_back = 1
```
For details about all available settings for configuring Xdebug, see [here](http://xdebug.org/docs/all_settings).

## Configuration
The following settings can be configured in Xdebug.sublime-settings or in *.sublime-project files:

*__path_mapping__*  
For remote debugging to resolve the file locations it is required to configure the path mapping with the server path as key and local path as value.

*__url__*  
Determine which URL to launch in the default web browser when starting/stopping a session.

*__ide_key__*  
An IDE key is used to identify with debugger engine when Sublime Text will start or stop a debugging session.

_This package does not filter sessions by IDE key, it will accept any IDE key, also ones that do not match this configured IDE key. It is merely used when launching the default web browser with the configured URL._

*__port__*  
Which port number Sublime Text should listen to connect with debugger engine.  

*__super_globals__*  
Show super globals in context view.  

*__max_children__*  
Maximum amount of array children and object's properties to return.  

*__max_data__*  
Maximum amount of variable data to initially retrieve.  

*__max_depth__*  
Maximum amount of nested levels to retrieve of array elements and object properties.  

*__break_on_start__*  
Break at first line on session start, when debugger engine has connected.  

*__break_on_exception__*  
Break on exceptions, suspend execution when the exception name matches an entry in this list value.  

*__close_on_stop__*  
Always close debug windows and restore layout on session stop.  

*__hide_password__*  
Do not show possible password values in context output.  

*__pretty_output__*  
Show in output parsed response instead of raw XML.  

*__launch_browser__*  
Always launch browser on session start/stop.

*This will only work if you have the '__url__' setting configured.*  

*__browser_no_execute__*  
When launching browser on session stop do not execute script.  
By using parameter XDEBUG_SESSION_STOP_NO_EXEC instead of XDEBUG_SESSION_STOP.  

*__disable_layout__*  
Do not use the debugging window layout.

*__debug_layout__*  
Window layout that is being used when debugging.  

*__breakpoint_group__*  
*__breakpoint_index__*  
*__context_group__*  
*__context_index__*  
*__stack_group__*  
*__stack_index__*  
*__watch_group__*  
*__watch_index__*  
Group and index positions for debug views.  

*__breakpoint_enabled__*  
*__breakpoint_disabled__*  
*__breakpoint_current__*  
*__current_line__*  
Custom gutter icons for indicating current line or enabled/disabled breakpoints.

_Do not use same icon for above values, because Sublime Text is unable to use the same icon for different scopes, in case there are duplicate icons detected it will fall back to the corresponding icon in the package._

*__python_path__*  
Path to Python installation on your system.  
Which is being used to load missing modules.  

*__debug__*  
Show detailed log information about communication between debugger engine and Sublime Text.  
  
---
  
Below are examples how to configure your Xdebug.sublime-settings and *.sublime-project files.

__Xdebug.sublime-settings__
```json
{
    "path_mapping": {
        "/absolute/path/to/file/on/server" : "/absolute/path/to/file/on/computer",
        "/var/www/htdocs/example/" : "C:/git/websites/example/"
    },
    "url": "http://your.web.server/index.php",
    "super_globals": true,
    "close_on_stop": true
}
```
__*.sublime-project__
```json
{
    "folders":
    [
        {
            "path": "..."
        }
    ],
    "settings":
    {
        "xdebug": {
            "path_mapping": {
                "/absolute/path/to/file/on/server" : "/absolute/path/to/file/on/computer",
                "/var/www/htdocs/example/" : "C:/git/websites/example/"
            },
            "url": "http://your.web.server/index.php",
            "super_globals": true,
            "close_on_stop": true
        }
    }
}
```

## Troubleshoot

#### Can I have both [SublimeTextXdebug](https://github.com/martomo/SublimeTextXdebug) and [SublimeXdebug](https://github.com/Kindari/SublimeXdebug) installed?
No. Having installed both packages can cause conflicts, because they might both listen to the same port for a debugger engine response and have similar keymapping.

However (project) settings from SublimeXdebug are compatible with SublimeTextXdebug.

#### How can I start a debugging session?
SublimeTextXdebug can [start or stop a debugging session](#startstop-debugging-session) by launching the default web browser with the configured URL and parameter `XDEBUG_SESSION_START` or `XDEBUG_SESSION_STOP` which uses the configured IDE key as value. By default the IDE key is `sublime.xdebug`.

When you do not configure the URL, the plugin will still listen for debugging connections from Xdebug, but you will need to trigger Xdebug [for a remote session](http://xdebug.org/docs/remote#starting).

If you want to run a start a debugging session from command line, before you run your script, you will need to set the environment variable __XDEBUG_CONFIG__ with the IDE key.

__Windows__
```
set XDEBUG_CONFIG="idekey=sublime.xdebug"
php myscript.php
```
__UNIX__
```
export XDEBUG_CONFIG="idekey=sublime.xdebug"
php myscript.php
```

Make sure before defining the environment variable you have switched to the proper user environment.  
As example you would set the environment variable as __guest__ and execute the script as __root__ _(sudo)_, then __root__ will not have the environment variable XDEBUG_CONFIG that was defined by __guest__.

#### How do I set a breakpoint and/or watch expression?
With SublimeTextXdebug you can easily [add/remove breakpoints](#breakpoints), which are send on session start.  
Or [set/edit/remove watch expressions](#watch-expressions), that are evaluated in the current execution context.  

Setting a conditional breakpoints or watch expressions is quite easy, it is like an __if__ statement in PHP.

As example you only want to stop on breakpoint when value of __$number__ is equal to __13__, then your __Breakpoint condition__ would be `$number==13`.  
Another example would be when you would like to know the value of __$item['image']__ on each break, then your __Watch expression__ would be `$item['image']`.

Another way is to set the breakpoint in your PHP code with the following function [`xdebug_break()`](http://xdebug.org/docs/remote#xdebug_break).

#### How to configure or disable breaking on exceptions?
By default the execution of a debugging session is suspended on each of the following exception names:
- __"Fatal error"__ - E_ERROR, E_CORE_ERROR, E_COMPILE_ERROR, E_USER_ERROR
- __"Catchable fatal error"__ - E_RECOVERABLE_ERROR (since PHP 5.2.0)
- __"Warning"__ - E_WARNING, E_CORE_WARNING, E_COMPILE_WARNING, E_USER_WARNING
- __"Parse error"__ - E_PARSE
- __"Notice"__ - E_NOTICE, E_USER_NOTICE
- __"Strict standards"__ - E_STRICT
- __"Deprecated"__ - E_DEPRECATED, E_USER_DEPRECATED (since PHP 5.3.0)
- __"Xdebug"__
- __"Unknown error"__

In order to specify which exception names to suspend the execution of a debugging session, configure the `break_on_exception` setting with a list of the specific exception names by choice from the list shown above.  

It is also possible to specify custom exceptions instead of __all__ exceptions (__"Fatal error"__). For example if you would configure __"MissingArgumentException"__ instead of __"Fatal error"__, it would not break on __"InvalidParameterException"__.

To disable breaking on exceptions either configure an empty list `break_on_exception: []` or set as `break_on_exception: false`.

#### How can I customize/disable the debugging layout?
Re-adjust the layout in Sublime Text to your liking and then in console (<kbd>Ctrl+\`</kbd>) you type `window.get_layout()` and set that value as your `debug_layout`.

Further customizing can be done by assigning the Xdebug views to a group/index with the `breakpoint_group`, `breakpoint_index`, `context_group`, `context_index`, `stack_group`, `stack_index`, `watch_group`, `watch_index` settings.

Or you can disable the debugging layout by setting `disable_layout: true`, which will open all Xdebug views in current active group/window on session start and does not change your layout.

#### How to solve `ImportError`?
Older versions of Sublime Text do not come with Python bundled and rely on your Python system installation.  
Some systems do not include specific modules which are required by this package, such as __pyexpat__.

Configure the `python_path` setting to the path of your Python installation on your system which is either newer or has all required modules. For example: `"python_path" : "/usr/lib/python2.7"`.

#### What to do when you experience any issues?
First check following _possible_ solutions that could resolve any issues:

- Use __absolute__ paths in your `path_mapping` setting, Xdebug does not return symbolic links.
- Breakpoint is on an empty line, Xdebug does not stop on empty lines.
- Set `port` and [xdebug.remote_port](http://xdebug.org/docs/all_settings#remote_port) to different port *(9001)*, default port 9000 might already be used by an other application.
- Add an exception for Sublime Text *(plugin_host.exe)* to your firewall, response from Xdebug could be blocked by firewall.
- Lower the `max_data`/`max_depth`/`max_children` settings to increase response speed or prevent crashing, Xdebug could return to much data to process.
- Change permissions for Sublime Text and it's packages on your filesystem, Sublime Text or package might not have valid rights.

Do you still experience any issues, then [create an issue](https://github.com/martomo/SublimeTextXdebug/issues/new) including the following data:

- What operation system(s) and version of Sublime Text are you using?
- How did you [install](https://github.com/martomo/SublimeTextXdebug#installation) SublimeTextXdebug, Package Control, git clone or download?
- Are you trying to debug the script remotely or locally, through browser or command line?
- Which version of Xdebug extension do you have?
- Can you post your [project/settings file](https://github.com/martomo/SublimeTextXdebug#configuration) and [Xdebug configuration](https://github.com/martomo/SublimeTextXdebug#xdebug) from the *.ini located on your server.
- Does the console window (<kbd>Ctrl+\`</kbd>) show any more information regarding the error?

## License

SublimeTextXdebug is released under the [MIT License](http://www.opensource.org/licenses/MIT).