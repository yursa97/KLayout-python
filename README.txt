To successfully use this library you should:
1. download this library from github/shamil777/BozonSampling
2. open KLayout, press 'Ctrl + F5' to open macros editor.
3. Right-click to the left panel and 'Add Location', choose path to the 'KLayout Macros' directory 
4. execute following code in the macro editor:
	import sys
	print( sys.path )
5. Copy output directories into the KLAYOUT_PYTHONPATH variable that is used to the KLayout interpreter.
	CAUTION: double backslashes as well as all types of quotes are prohibited!!!
6. Add to KLAYOUT_PYTHONPATH environment variable path to the 'KLayout Macros' directory you have downloaded.
7. Have fun!!!
