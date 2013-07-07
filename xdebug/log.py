import sublime
import logging
import os

# Settings variables
try:
    from . import settings as S
except:
    import settings as S


def clear_output():
    # Clear previous output file and configure logging module
    output_file = os.path.join(sublime.packages_path(), 'User', S.FILE_LOG_OUTPUT)
    logging.basicConfig(filename=output_file, filemode='w', level=logging.DEBUG, format='[%(asctime)s] %(levelname)s - %(message)s', datefmt='%m/%d/%Y %I:%M:%S%p')


def debug(message=None):
    debug = S.get_project_value('debug') or S.get_package_value('debug') or S.DEBUG
    if not debug or message is None:
        return
    # Write message to console and output file
    print(message)
    logging.debug(message)


def info(message=None):
    if message is None:
        return
    logging.info(message)