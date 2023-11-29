#!/usr/bin/env python3

import configparser
import logging
import os

import connexion
from connexion.resolver import RestyResolver
import sys

logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, format="'%(name)s:%(lineno)s' | %(message)s"
)

logger = logging.getLogger(os.path.basename(__file__))

app_dirname = os.path.dirname(os.path.abspath(__file__))


def load_config(plugin=None):
    config = configparser.ConfigParser()
    if plugin:
        config_file = os.path.join(
            app_dirname,
            "plugins/%s/config.ini" % plugin
        )
    else:
        config_file = os.path.join(app_dirname, "config.ini")
        if "CONFIG_FILE" in os.environ:
            config_file = os.getenv("CONFIG_FILE")

    try:
        config.read_file(open(config_file))
        logging.debug("Main configuration successfully loaded: %s" % config_file)
    except configparser.MissingSectionHeaderError as e:
        message = "Could not find main config file: %s" % config_file
        logging.error(message)
        logging.debug(e)
        error = {"code": 500, "message": "%s" % message}
        logging.debug("Returning API response: %s" % error)
        return json.dumps(error), 500

    return config


if __name__ == "__main__":
    app = connexion.FlaskApp(__name__)
    app.add_api(
        "fair-api.yaml",
        arguments={"title": "FAIR evaluator Example"},
        resolver=RestyResolver("api"),
    )
    app.run(port=9090)
