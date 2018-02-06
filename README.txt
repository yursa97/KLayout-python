To successfully use this library you should:
1. download this library from github/shamil777/KLayout-python
2. open KLayout, press 'Ctrl + F5' to open macros editor.
3. In macros editor window: right-click to the left panel and choose 'Add Location', choose path to the 'KLayout-python' directory 
4. Create KLAYOUT_PYTHONPATH environment variable (this variable is used by KLayout python interpreter)
5. Execute following code in the macro editor:
	import sys
	print( sys.path )
6. Copy output directories into the KLAYOUT_PYTHONPATH variable that is used to the KLayout interpreter.
	CAUTION: double backslashes as well as all types of quotes are prohibited!!!
7. Add to KLAYOUT_PYTHONPATH environment variable path to the 'KLayout-python' directory you have downloaded.
8. Have fun!!!
