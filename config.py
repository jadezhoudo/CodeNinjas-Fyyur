import os
SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'postgresql://chaudo@localhost:5432/chaudn1'
SQLALCHEMY_TRACK_MODIFICATIONS = False
