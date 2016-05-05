import sys

sys.dont_write_bytecode=True

import os
from mino import app

if hasattr(sys, 'frozen'):
  pypath = os.path.dirname(sys.executable)
  pypath = os.path.join(pypath,'library.zip')
  import zipimport
  imp = zipimport.zipimporter(pypath)
else:
  pypath = os.path.dirname(__file__)
  import imp
  
app.start_server(pypath,imp)
