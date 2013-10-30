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
* Overview of breakpoints in all files and disable/enable breakpoints with simple click
* Debugging layout for stack history and context variables with syntax
* Evaluate a given string within the current execution context
* Inspect (nested) context variables
* Set conditional breakpoints
* Works on both Sublime Text 2 __and__ 3

#### Upcoming/Scheduled features
* Show global/class context variables
* Option for defining debug layout in settings

## Commands
Here is a complete list of commands you can find Command Pallette under the `Xdebug` namespace or in the menu under `Tools / Xdebug`:

#### Start/Stop debugging session
* Start Debugging - <kbd>Ctrl+Shift+F9</kbd>
* Start Debugging (Launch Browser)
* Stop Debugging - <kbd>Ctrl+Shift+F10</kbd>
* Stop Debugging (Launch Browser)
* Stop Debugging (Close Windows)

*__Launch Browser__ menu option will only show if you have an url configured within [settings](#configuration).*

#### Breakpoints
* Add/Remove Breakpoint - <kbd>Ctrl+F8</kbd>
* Set Conditional Breakpoint - <kbd>Shift+F8</kbd>
* Clear All Breakpoints

#### Session commands
* Evaluate
* Execute
* Status

#### Continuation commands
* Run - <kbd>Ctrl+Shift+F5</kbd>
* Step Over - <kbd>Ctrl+Shift+F6</kbd>
* Step Into - <kbd>Ctrl+Shift+F7</kbd>
* Step Out - <kbd>Ctrl+Shift+F8</kbd>
* Stop
* Detach

#### Other
* Reset Layout - <kbd>Ctrl+Shift+F11</kbd>
* Settings

*__Settings__ will show current user settings, when none available it will generate a template.*

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

*__ide_key__*  
An IDE key is used to identify with debugger engine when Sublime Text will start or stop a debugging session.

_This package does not filter sessions by IDE key, it will accept any IDE key, also ones that do not match this configured IDE key. It is merely used when launching the default web browser with the configured URL._

*__url__*  
Determine which URL to launch in the default web browser when starting/stopping a session.

*__port__*  
Which port number Sublime Text should listen to connect with debugger engine.  

*__close_on_stop__*  
Always close debug windows and restore layout on session stop.  

*__max_children__*  
Maximum amount of array children and object's properties to return.  

*__max_depth__*  
Maximum amount of nested levels to retrieve of array elements and object properties.  

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
    "ide_key": "sublime.xdebug",
    "url": "http://your.web.server",
    "port": 9000,
    "close_on_stop": true,
    "max_depth": 3,
    "max_children": 32,
    "debug": true
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
            "ide_key": "sublime.xdebug",
            "url": "http://your.web.server",
            "port": 9000,
            "close_on_stop": true,
            "max_depth": 3,
            "max_children": 32,
            "debug": true
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

If you do not configure the URL, the plugin will still listen for debugging connections from Xdebug, but you will need to trigger Xdebug [for a remote session](http://xdebug.org/docs/remote#starting).

#### How do I set a breakpoint?
* With SublimeTextXdebug you can [add/remove breakpoints](#breakpoints), which are send on session start.
* Another way is to set the breakpoint in your PHP code with the following function [`xdebug_break()`](http://xdebug.org/docs/remote#xdebug_break).

## License

SublimeTextXdebug is released under the [MIT License](http://www.opensource.org/licenses/MIT).
