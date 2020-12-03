import click
from flask import Flask
import sys

cli = sys.modules['flask.cli']
cli.show_server_banner = lambda *x: click.echo(
    "\n" +
    "╔════════════════════════╗\n" +
    "▉ JustEmuTarkov (Py.0.1) ▉\n" +
    "╚════════════════════════╝\n")

# Logger Editor
from logging.config import dictConfig

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s:\n  %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})
# End of Logger Editor

app = Flask(__name__)

