# Helper class
try:
	from .helper import H
except:
	from helper import H


# Global variables
try:
	from . import settings as S
except:
	import settings as S


# Modules to be imported from package when using *
__all__ = ['dbgp','H','S','session','util']