#!/usr/bin/env python
from flask.ext.script import Manager, Server
from flask.ext.assets import ManageAssets
from apollo import app, assets

manager = Manager(app)
manager.add_command('run', Server())
manager.add_command('assets', ManageAssets(assets))

if __name__ == '__main__':
    manager.run()
