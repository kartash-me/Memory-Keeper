import os
import sys

from functions import dotenv


INTERP = os.path.expanduser(dotenv("VENV_PATH"))

if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.append(os.getcwd())

from app import app as application
