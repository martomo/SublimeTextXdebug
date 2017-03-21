import sys

# Get python version
python_version = sys.version_info[:2]


# Define helper class according to python version 
if (python_version <= (2, 6)):
	# Version 2.6 and below
	import helper_26 as H
elif (python_version == (2, 7)):
	# Version 2.7
	from . import helper_27 as H
else:
	# Version 3+
	from . import helper as H


# Modules to be imported from package when using *
__all__ = ['H']