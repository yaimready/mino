import sys

sys.dont_write_bytecode=True

from mino import app

app.start_server('.')
