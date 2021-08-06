#!/usr/bin/env python3
import logging

import connexion
from connexion.resolver import RestyResolver
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

if __name__ == '__main__':
    app = connexion.FlaskApp(__name__)
    app.add_api('fair-api.yaml',
                arguments={'title': 'FAIR evaluator Example'},
                resolver=RestyResolver('api'))
    app.run(port=9090)
