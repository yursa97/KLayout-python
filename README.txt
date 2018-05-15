To successfully use this library you should:
1. download this library from github/shamil777/KLayout-python
2. open KLayout, press 'Ctrl + F5'(Windows) 'F5'(MacOS) to open macros editor.
3. Locate left panel with some libraries folders. Right above this panel you may change programming language you are using. Switch to python.
4. In macros editor window: right-click to the left panel (the panel with libraries folder) and choose 'Add Location', choose path to the 'KLayout-python' directory 
5. Create KLAYOUT_PYTHONPATH environment variable (this variable is used by KLayout python interpreter)
6. Execute following code in the macro editor:
	import sys
	print( sys.path )
7. Copy output directories into the KLAYOUT_PYTHONPATH variable that is used to the KLayout interpreter.
	CAUTION: double backslashes as well as all types of quotes are prohibited!!!
8. Add to KLAYOUT_PYTHONPATH environment variable path to the 'KLayout-python' directory you have downloaded.
9. Have fun!!!
