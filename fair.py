#!/usr/bin/env python3

import configparser
import logging
import os
import sys

import connexion
from connexion.resolver import RestyResolver

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG,
    format="%(levelname)s:'%(name)s:%(lineno)s' | %(message)s",
)
logger = logging.getLogger("api")

app_dirname = os.path.dirname(os.path.abspath(__file__))


def load_config(plugin, fail_if_no_config=True):
    config_file_main = os.path.join(app_dirname, "config.ini")
    config_file_plugin = os.path.join(app_dirname, "plugins/%s/config.ini" % plugin)

    config = configparser.ConfigParser(config_file_main, config_file_plugin)
    # if plugin:
    #     config_file = os.path.join(app_dirname, "plugins/%s/config.ini" % plugin)
    # else:
    #     config_file = os.path.join(app_dirname, "config.ini")
    #     if "CONFIG_FILE" in os.environ:
    #         config_file = os.getenv("CONFIG_FILE")

    try:
        config.read_file(open(config_file))
        logging.debug("Main configuration successfully loaded: %s" % config_file)
    except FileNotFoundError as e:
        logging.error("Could not load config file: %s" % str(e))
        if fail_if_no_config:
            raise (e)
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
