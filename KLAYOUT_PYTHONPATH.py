
# Enter your Python code here

import sys
import os
import re
print(sys.path,"\n")
klayout_pythonpath = ""
for element in sys.path:
    new_element = re.sub(r"\\",r"\\",element)
    klayout_pythonpath += new_element + ";"

print(klayout_pythonpath + os.path.dirname(__file__))
