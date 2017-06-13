"""This module simply prints hello ElasTest."""
from os import getenv
from flask import Flask


HELLO_APP = Flask(__name__)


@HELLO_APP.route("/")
def hello():
    """just a basic hello!"""
    return "Hello ElasTest!"

if __name__ == "__main__":
    P = getenv('ESM_PORT', 8080)
    HELLO_APP.run(port=P)
