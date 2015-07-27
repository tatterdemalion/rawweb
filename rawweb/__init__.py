#!/usr/bin/env python
from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.script import Manager
from flask.ext.migrate import Migrate, MigrateCommand


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'output/'
app.config['HOST'] = 'http://localhost:5000/'
app.config['MEDIA_HOST'] = 'http://localhost:5001/'
app.config.from_envvar('RAWWEB_SETTINGS')

db = SQLAlchemy(app)
import rawweb.models

migrate = Migrate(app, db)
manager = Manager(app)
manager.add_command('db', MigrateCommand)

import rawweb.api
