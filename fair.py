#!/usr/bin/env python3
import logging
import os

import connexion
from connexion.resolver import RestyResolver
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='\'%(name)s:%(lineno)s\' | %(message)s')

logger = logging.getLogger(os.path.basename(__file__))

app_dirname = os.path.dirname(os.path.abspath(__file__))

if __name__ == '__main__':
    app = connexion.FlaskApp(__name__)
    app.add_api('fair-api.yaml',
                arguments={'title': 'FAIR evaluator Example'},
                resolver=RestyResolver('api'))
    app.run(port=9090)
