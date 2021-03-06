# pylint: disable=unused-import

import os
import shutil
import click
import numpy as np
from flask import Flask, redirect
from flask.json import JSONEncoder

import minerva.models
import minerva.database as database
from minerva.config import DATABASE_PATH, ROOT_DIR, MIGRATION_DIR
from minerva.config import config, prepare_directory
from minerva.database import init_db, db
from minerva.controllers import dataset_route
from minerva.controllers import project_route
from minerva.controllers import system_route

static_path = os.path.join(os.path.dirname(__file__), 'dist')
app = Flask(__name__, static_folder=static_path)
for name, val in config.items():
    app.config[name] = val
app.url_map.strict_slashes = False


# enable to return ndarray in json
class CustomJSONEncoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.floating):
            return float(o)
        if isinstance(o, np.ndarray):
            return o.tolist()
        return JSONEncoder.default(self, o)


app.json_encoder = CustomJSONEncoder

# initialize database
init_db(app)

# create minerva directory
prepare_directory()

# API endpoints
app.register_blueprint(dataset_route, url_prefix='/api/datasets')
app.register_blueprint(project_route, url_prefix='/api/projects')
app.register_blueprint(system_route, url_prefix='/api/system')


# proxy
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def send_file(path):
    if path in ['', '/']:
        return redirect('/projects')
    if path.find('favicon.ico') > -1:
        path = 'favicon.ico'
    elif path.find('.js') == -1:
        path = 'index.html'
    return app.send_static_file(path)


@click.group()
def cli():
    pass


@cli.command()
@click.option('--host', '-h', default='0.0.0.0')
@click.option('--port', '-p', default=9000)
def run(host, port):
    # create databse if not exists
    if not os.path.exists(DATABASE_PATH):
        with app.app_context():
            db.create_all()
            database.init_migration(MIGRATION_DIR)
            database.create_migration(MIGRATION_DIR)

    # start server
    app.run(debug=True, host=host, port=int(port))


@cli.command()
def create_db():
    with app.app_context():
        db.create_all()


@cli.command()
def upgrade_db():
    with app.app_context():
        database.create_migration(MIGRATION_DIR)
        database.upgrade_db(MIGRATION_DIR)


@cli.command()
def downgrade_db():
    with app.app_context():
        database.downgrade_db(MIGRATION_DIR)


@cli.command()
def clean():
    shutil.rmtree(ROOT_DIR)


if __name__ == '__main__':
    cli()
