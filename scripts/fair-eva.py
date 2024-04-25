#!/usr/bin/env python3

"""
# Full example
python3 scripts/fair-eva.py --id 1b67c7f4-3cb8-473e-91a9-0191a1fa54a8 --plugin epos -B https://www.ics-c.epos-eu.org/api/v1

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
        description=("Command-line interface for FAIR EVA tool")
    )
    parser.add_argument(
        "-i",
        "--id",
        metavar="IDENTIFIER",
        type=str,
        help="Identifier of the (meta)data",
    )
    parser.add_argument(
        "-p", "--plugin", metavar="PLUGIN", type=str, help="FAIR EVA plugin name"
    )
    parser.add_argument(
        "-r",
        "--repository",
        metavar="URL",
        type=str,
        help="(meta)data repository endpoint",
    )
    parser.add_argument("-s", "--scores", action="store_true")
    parser.add_argument(
        "--api-endpoint",
        metavar="URL",
        type=str,
        default="http://localhost:9090/v1.0/rda/rda_all",
        help=(
            "Endpoint to perform HTTP request. Example: "
            "http://localhost:9090/v1.0/rda/rda_all"
        ),
    )
    parser.add_argument("-fs", "--full-scores", action="store_true")
    parser.add_argument("-j", "--json", action="store_true")

    parser.add_argument(
        "-q", "--query", metavar="QUERY", type=str, help="data asset to look for"
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


def search(keytext):
    args = get_input_args()
    max_tries = 5

    headers = {
        "accept": "application/json",
    }
    good = 0
    params = {"facets": "false", "q": keytext}
    print(args.query)
    response = requests.get(
        "https://ics-c.epos-ip.org/development/k8s-epos-deploy/dt-geo/api/v1/resources/search",
        params=params,
        headers=headers,
    )
    terms = response.json()
    # print(response.json())
    # print(terms.keys())
    # print(terms['filters'])
    # print(len(terms['results']['distributions']))
    print(terms["results"]["distributions"][0])
    # print(terms['results']['distributions'][0]['title'])
    number_of_items = len(terms["results"]["distributions"])
    for index in range((len(terms["results"]["distributions"]))):
        print(index, (terms["results"]["distributions"][index]["title"]))
    for j in range(max_tries):
        ind = input(
            "Please choose the index of the item you want to evaluate. From 0 to "
            + str(len(terms["results"]["distributions"]))
            + " "
        )
        try:
            if int(ind) > (-1) and int(ind) < number_of_items:
                good = 1
        except:
            print("Please introduce an integer between 0 and " + str(number_of_items))
        if good == 1:
            break
    if good == 0:
        print("Max tries , restart program")
        return ()
    return terms["results"]["distributions"][int(ind)]["id"]


def main():
    logging.basicConfig(level=logging.INFO)

    args = get_input_args()
    url = args.api_endpoint

    if args.repository == None:
        response = requests.get(
            "http://localhost:9090/v1.0/endpoints?plugin=" + args.plugin
        )
        if response.status_code == 404:
            print(
                "Input plugin not found. Look for plugins in the plugins folder. The accepted plugins for this script are: "
                + str(response.json())
            )
            return "Input plugin not found"
        else:
            metadata_endpoint = response.json()
    else:
        metadata_endpoint = args.repository

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
    if args.query:
        identifier = search(args.query)
    else:
        identifier = args.id

    headers = {"Content-Type": "application/json"}
    data = {
        "id": identifier,
        "repo": args.plugin,
        "oai_base": metadata_endpoint,
        "lang": "EN",
    }

    r = requests.post(url, data=json.dumps(data), headers=headers)

    if args.json or not (args.scores or args.full_scores):
        print(r.json())
    else:
        result = json.loads(r.text)

        if args.scores or args.full_scores:
            print("\n")
            calcpoints(
                result[identifier],
                print_scores=args.scores,
                print_fullscores=args.full_scores,
            )
    if args.query or not args.repository:
        print("For a faster execution you may use: ")
        command = (
            "python3 scripts/fair-eva.py --id "
            + identifier
            + " --plugin epos -r "
            + metadata_endpoint
        )
        if args.json:
            command += " -j "
        if args.scores:
            command += " -s "
        if args.full_scores:
            command += " -fs "
        print(command)


main()
