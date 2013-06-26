# SublimeTextXdebug
Xdebug debugger client integration for Sublime Text.

Based on the [SublimeXdebug](https://github.com/Kindari/SublimeXdebug) package by [Kindari](https://github.com/Kindari).

## Features
* Remote debugging by configuring path mapping
* Navigate on breakpoint hit to relevant file on specific line, when found on local drive
* Debugging layout for stack history and context variables with syntax
* Inspect (nested) context variables
* Works on both Sublime Text 2 and 3

### Upcoming/Scheduled features
* Conditional breakpoints
* Show global and class context variables
* Option for defining debug/default layout in settings
* Debug window for showing breakpoints in file

## Commands
Here is a complete list of commands you can find Command Pallette under the `Xdebug` namespace or in the menu under `Tools`:

### Start/Stop debugging session
* Start Debugging - <kbd>Ctrl+Shift+F9</kbd>
* Start Debugging (Launch Browser)
* Stop Debugging - <kbd>Ctrl+Shift+F10</kbd>
* Stop Debugging (Launch Browser)
* Stop Debugging (Close Windows)

*__Launch Browser__ menu option will only show if you have an url configured in settings.*

### Breakpoints
* Add/Remove Breakpoint - <kbd>Ctrl+F8</kbd>
* Clear All Breakpoints

### Session commands
* Execute
* Status

### Continuation commands
* Run - <kbd>Ctrl+Shift+F5</kbd>
* Step Over - <kbd>Ctrl+Shift+F6</kbd>
* Step Into - <kbd>Ctrl+Shift+F7</kbd>
* Step Out - <kbd>Ctrl+Shift+F9</kbd>
* Stop
* Detach

### Other
* Reset Layout - <kbd>Ctrl+Shift+F11</kbd>
* Settings

*__Settings__ will show current user settings, when none available it will generate a template.*

## Installation
Execute the following command in your Sublime Packages folder:
```git clone https://github.com/martomo/SublimeTextXdebug.git Xdebug``` 

### Xdebug
In order to be able to debug, you will need have Xdebug installed.
[See here for installation instructions](http://xdebug.org/docs/install)

Below is a configuration template for php.ini/xdebug.ini, be warned if you are on a Live environment, __remote_connect_back__ (since Xdebug version 2.1) allows every debug request from any source to be accepted.

```ini
[xdebug]
zend_extension = /absolute/path/to/your/xdebug-extension.so
xdebug.remote_enable = 1
xdebug.remote_host = "127.0.0.1"
xdebug.remote_port = 9000
xdebug.remote_handler = "dbgp"
xdebug.remote_mode = req
xdebug.remote_connect_back = 1
```

## Configuration
This plugin can initiate or terminate a debugging session by launching your default web browser and sending a web request to the configured URL with the following parameters XDEBUG_SESSION_START or XDEBUG_SESSION_STOP together with an IDE key.

For remote debugging to resolve the file locations it is required to configure the path mapping with the server path as key and local path as value.

The debug URL, port, IDE key and path mapping are defined in your Xdebug.sublime-settings file like this:
```
{
	"path_mapping": {
		"/path/to/file/on/server" : "/path/to/file/on/computer",
		"/var/www/htdocs/example/" : "C:/git/websites/example/"
	},
    "ide_key": "your_custom_ide_key", 
    "url": "http://your.web.server", 
    "port": 9000
}
```

If you do not configure the URL, the plugin will still listen for debugging connections from Xdebug, but you will need to trigger Xdebug [for a remote session](http://xdebug.org/docs/remote). By default the URL will use `sublime.xdebug` as IDE key.

## License

SublimeTextXdebug is released under the [MIT License](http://www.opensource.org/licenses/MIT).