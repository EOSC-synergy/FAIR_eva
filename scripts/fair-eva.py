#!/usr/bin/env python3

"""
# Full example
python3 scripts/fair-eva.py -ID 1b67c7f4-3cb8-473e-91a9-0191a1fa54a8 -R epos -B https://www.ics-c.epos-eu.org/api/v1

# EXAMPLES
# EPOS Production API
id = "12b76f8e-d10e-4c5d-a113-4855f6bc3435"
oaibase = "https://www.ics-c.epos-eu.org/api/v1"
repo = "epos"

# EPOS prototype API
oaibase =  'https://ics-c.epos-ip.org/development/k8s-epos-deploy/dt-geo/api/v1'
ide = '46676a31-fa8e-4a4a-a3c0-15d689783a08'

# DIGITAL CSIC
id = "http://hdl.handle.net/10261/157765"
oaibase = "http://digital.csic.es/dspace-oai/request"
repo = "oai-pmh"
"""

import argparse
import json
import logging
import requests
import socket
import sys
import time
from flask_babel import Babel, gettext, lazy_gettext as _l


def get_input_args():
    parser = argparse.ArgumentParser(
        description=("Prepare requests for FAIR assessment tool")
    )
    parser.add_argument("-ID", metavar="ID", type=str, help="Persistent Identifier")
    parser.add_argument("-R", metavar="PLUGIN", type=str, help="HTTP method")
    parser.add_argument("-B", metavar="OAI-PMH", type=str, help="OAI-PMH_ENDPOINT")

    parser.add_argument("--s", action="store_true")
    parser.add_argument("--fs", action="store_true")
    parser.add_argument(
        "--tool_endpoint",
        metavar="ENDPOINT",
        type=str,
        default="http://localhost:9090/v1.0/rda/rda_all",
        help=(
            "Enpoint to perform HTTP request. Example: "
            "http://localhost:9090/v1.0/rda/rda_all"
        ),
    )

    return parser.parse_args()


def is_port_open():
    is_port_open = False
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(("127.0.0.1", 9090))
    if result == 0:
        is_port_open = True
    sock.close()

    return is_port_open


def calcpoints(result, print_scores=False, print_fullscores=False):
    keys = ["findable", "accessible", "interoperable", "reusable", "total"]
    values = [0, 0, 0, 0, 0]
    result_points = 0
    weight_of_tests = 0
    points = dict(zip(keys, values))

    for key in keys[:-1]:
        g_weight = 0
        g_points = 0
        for kk in result[key]:
            result[key][kk]["indicator"] = gettext(
                "%s.indicator" % result[key][kk]["name"]
            )

            if print_fullscores == True:
                print(
                    "In "
                    + str(kk)
                    + " your item has "
                    + str(result[key][kk]["points"])
                    + " points"
                )
            result[key][kk]["name_smart"] = gettext("%s" % result[key][kk]["name"])

            weight = result[key][kk]["score"]["weight"]
            weight_of_tests += weight
            g_weight += weight
            result_points += result[key][kk]["points"] * weight
            g_points += result[key][kk]["points"] * weight

        points[key] = round((g_points / g_weight), 3)
    points["total"] = round((result_points / weight_of_tests), 2)
    if print_scores == True:
        printpoints(points)
    return points


def printpoints(
    points,
):
    for key in points.keys():
        print("In " + str(key) + " your item has " + str(points[key]) + " points")


def main():
    logging.basicConfig(level=logging.INFO)

    args = get_input_args()
    url = args.tool_endpoint

    is_api_running = False
    for i in range(1, 5):
        if is_port_open():
            logging.debug("FAIR-eva API running on port 9090")
            is_api_running = True
            break
        else:
            logging.debug("FAIR-eva API not running: port 9090 not open")
            logging.debug("Sleeping for 5 seconds..")
            time.sleep(5)
    if not is_api_running:
        logging.error("FAIR-eva API was not able to launch: exiting")
        sys.exit(-1)

    headers = {"Content-Type": "application/json"}
    data = {"id": args.ID, "repo": args.R, "oai_base": args.B, "lang": "ES"}

    r = requests.post(url, data=json.dumps(data), headers=headers)
    result = json.loads(r.text)
    print(result)
    calcpoints(result[args.ID], print_scores=args.s, print_fullscores=args.fs)


main()
