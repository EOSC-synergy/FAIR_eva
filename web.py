#!/usr/bin/env python3
import argparse
import configparser
import json
import logging
import os.path
import sys
from math import pi

import numpy as np
import pandas as pd
import requests
from bokeh.embed import components
from bokeh.layouts import row
from bokeh.models import ColumnDataSource, LabelSet
from bokeh.plotting import figure
from bokeh.transform import cumsum
from flask import (
    Flask,
    g,
    make_response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_babel import Babel, gettext
from flask_babel import lazy_gettext as _l
from flask_wtf import FlaskForm
from wtforms import SelectField, StringField

import api.utils as ut
import utils.pdf_gen as pdf_gen
from utils.smart_plugin import Smart_plugin

logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, format="'%(name)s:%(lineno)s' | %(message)s"
)

logger = logging.getLogger(os.path.basename(__file__))


def set_parser():
    parser = argparse.ArgumentParser(
        description="FAIR EVA (Evaluator, Validator & Advisor)"
    )
    current_folder = os.path.dirname(os.path.realpath(__file__))
    sample_config = os.path.join(os.path.dirname(current_folder), "config.ini.template")
    parser.add_argument(
        "-c",
        "--config",
        metavar="CONFIG_FILE",
        dest="config_file",
        default="config.ini",
        help="Main configuration file (default: config.ini). "
        "For a complete example, please check <%s>" % sample_config,
    )

    return parser.parse_args()


options_cli = set_parser()
config = configparser.ConfigParser()
config.read(options_cli.config_file)

app = Flask(__name__)
app.config.update(
    {
        "SECRET_KEY": "sdafasfwefq3egthyjtyhwef",
        "TESTING": True,
        "LOGO_URL": config["local"]["logo_url"],
        "TITLE": config["local"]["title"],
        "DEBUG": True,
        "FLASK_DEBUG": 1,
        "PATHS": ["about_us", "evaluator", "export_pdf", "evaluations"],
        "BABEL_DEFAULT_LOCALE": "es",
        "BABEL_LOCALES": [
            "en",
            "en-CA",
            "en-IE",
            "en-GB",
            "en-US",
            "es",
            "es-ES",
            "es-MX",
        ],
    }
)

babel = Babel(app)
IMG_FOLDER = "/static/img/"


@app.before_request
def get_global_language():
    g.babel = babel
    success_message = _l("Test")
    g.language = get_locale()


def get_locale():
    lang = request.path[1:].split("/", 1)[0]

    if lang in app.config["BABEL_LOCALES"]:
        session["lang"] = lang
        return lang

    if lang_in_session():
        return session.get("lang")

    default_lang = fallback_lang()
    session["lang"] = default_lang
    return default_lang


babel.init_app(app, locale_selector=get_locale)


def lang_in_session():
    return (
        session.get("lang") is not None
        and session.get("lang") in app.config["BABEL_LOCALES"]
    )


def fallback_lang():
    best_match = request.accept_languages.best_match(app.config["BABEL_LOCALES"])

    if best_match is None:
        return app.config["BABEL_DEFAULT_LOCALE"]

    if "en" in best_match:
        return "en"

    return "es"


@app.route("/", defaults={"path": ""}, methods=["GET", "POST"])
@app.route("/<path:path>", methods=["GET", "POST"])
def catch_all(path):
    if path == "":
        return redirect(url_for("home_" + g.language))
    subpaths = path.split("/")
    if len(subpaths) > 2:
        subpaths.pop(0)
    if subpaths[0] in app.config["BABEL_LOCALES"]:
        if len(subpaths) > 1:
            if subpaths[1] in app.config["PATHS"]:
                return redirect(
                    url_for(subpaths[1] + "_" + subpaths[0], **request.args)
                )
            else:
                return redirect(url_for("not-found_" + subpaths[0]))
        else:
            return redirect(url_for("home_" + subpaths[0]))
    else:
        if subpaths[0] in app.config["PATHS"]:
            return redirect(url_for(subpaths[0] + "_" + g.language, **request.args))
        else:
            if len(subpaths) > 1:
                if subpaths[1] in app.config["PATHS"]:
                    return redirect(
                        url_for(subpaths[1] + "_" + g.language, **request.args)
                    )
            else:
                return redirect(url_for("not-found_" + g.language))


@app.route("/es", endpoint="home_es")
@app.route("/en", endpoint="home_en")
def index():
    form = CheckIDForm(request.form)
    aditional_params = False
    return render_template("index.html", form=form, aditional_params=aditional_params)


@app.route("/es/not-found", endpoint="not-found_es")
@app.route("/en/not-found", endpoint="not-found_en")
def not_found():
    return render_template("not-found.html")


@app.route("/es/about_us", endpoint="about_us_es")
@app.route("/en/about_us", endpoint="about_us_en")
def about_us():
    if session.get("lang") == "es":
        return render_template("acerca_de.html")
    else:
        return render_template("about_us.html")


@app.route("/es/evaluations", endpoint="evaluations_es")
@app.route("/en/evaluations", endpoint="evaluations_en")
def evaluations():
    if session.get("lang") == "es":
        return render_template("evaluaciones.html")
    else:
        return render_template("evaluations.html")


@app.route("/es/evaluator", endpoint="evaluator_es", methods=["GET", "POST"])
@app.route("/en/evaluator", endpoint="evaluator_en", methods=["GET", "POST"])
def evaluator():
    app.config["BABEL_TRANSLATION_DIRECTORIES"] = "translations"
    logging.debug(app.config["BABEL_TRANSLATION_DIRECTORIES"])
    babel.init_app(app, locale_selector=get_locale)
    try:
        args = request.args
        oai_base = None
        item_id = args["item_id"]
        logger.debug("ARGS_evaluator: %s" % args)
        sp = Smart_plugin(config["Repositories"])
        if item_id is None or item_id == "":
            form = CheckIDForm(request.form)
            aditional_params = True
            return render_template(
                "index.html", form=form, aditional_params=aditional_params
            )
        if config["local"]["only_local"] == "True":
            logger.debug("Only local TRUE")
            repo = config["local"]["repo"]
        elif "repo" not in args:
            plugin, url = sp.doi_flow(args["item_id"])
            repo = plugin
            oai_base = url
        else:
            logger.debug("Only local FALSE")
            repo = args["repo"]

        if repo is None:
            form = CheckIDForm(request.form)
            aditional_params = True
            return render_template(
                "index.html", form=form, aditional_params=aditional_params
            )

        logger.debug("ITEM_ID: %s | REPO: %s" % (item_id, repo))
        result_points = 0
        num_of_tests = 41

        findable = {}
        accessible = {}
        interoperable = {}
        reusable = {}
        if oai_base is None:
            oai_base = repo_oai_base(repo)
        logger.debug("OAI_BASE: %s" % oai_base)

        try:
            if "oai_base" in args:
                if args["oai_base"] != "" and ut.check_url(
                    args["oai_base"] + "?verb=Identify"
                ):
                    oai_base = args["oai_base"]
                    logger.debug("Aqui OAI: %s" % oai_base)
            else:
                if ut.check_url(oai_base + "?verb=Identify") == False:
                    oai_base = ""
                    logger.debug("Aqui OAI: %s" % oai_base)
        except Exception as e:
            logger.error("Problem getting args")
        logger.debug("SESSION LANG: %s" % session.get("lang"))
        body = json.dumps(
            {
                "id": item_id,
                "repo": repo,
                "oai_base": oai_base,
                "lang": session.get("lang"),
            }
        )
        logger.debug("BODY: %s" % body)
    except Exception as e:
        logger.error("Problem creating the object")
        logger.error(e)

    try:
        logging.debug(
            "Checking translation availability at plugins/%s/translations" % repo
        )
        if os.path.exists("plugins/%s/translations" % repo):
            app.config["BABEL_TRANSLATION_DIRECTORIES"] = (
                "plugins/%s/translations" % repo
            )
            logging.debug(app.config["BABEL_TRANSLATION_DIRECTORIES"])
            babel.init_app(app, locale_selector=get_locale)
        url = "http://localhost:9090/v1.0/rda/rda_all"
        result = requests.post(
            url, data=body, headers={"Content-Type": "application/json"}
        )
        logger.debug("RDA_ALL test completed")
        resultis = result.json()
        for key in resultis:
            result = resultis[key]
        result_points = 0
        weight_of_tests = 0
        for key in result:
            g_weight = 0
            g_points = 0
            if key != "data_test":
                logger.debug("Parsing: %s" % result[key])
                for kk in result[key]:
                    logger.debug("---- %s" % kk)
                    result[key][kk]["indicator"] = gettext(
                        "%s.indicator" % result[key][kk]["name"]
                    )
                    result[key][kk]["name_smart"] = gettext(
                        "%s" % result[key][kk]["name"]
                    )
                    # pesos
                    weight = result[key][kk]["score"]["weight"]
                    weight_of_tests += weight
                    g_weight += weight
                    result_points += result[key][kk]["points"] * weight
                    g_points += result[key][kk]["points"] * weight
                result[key].update(
                    {
                        "result": {
                            "points": round((g_points / g_weight), 2),
                            "color": ut.get_color(round((g_points / g_weight), 2)),
                        }
                    }
                )
                logger.debug(
                    "%s has %f points and %s color"
                    % (
                        key,
                        round((g_points / g_weight)),
                        ut.get_color(round((g_points / g_weight), 2)),
                    )
                )

        result_points = round((result_points / weight_of_tests), 2)
    except Exception as e:
        logger.error("Problem parsing API result")
        logger.error(e)
        error_message = "%s: %s" % (gettext("PID_problem_2"), item_id)
        if ut.is_persistent_id(item_id):
            id_list = ut.get_persistent_id_type(item_id)
            error_message = "%s | %s %s" % (
                gettext("Problem accessing data and metadata. Please, try again"),
                gettext("PID_problem_1"),
                str(id_list),
            )
            error_message = (
                error_message
                + " | "
                + gettext("PID_problem_3")
                + ". "
                + gettext("PID_problem_4")
                + ":"
            )
            for e in id_list:
                error_message = error_message + " " + ut.pid_to_url(item_id, e)

        logger.error(error_message)
        return render_template("error.html", error_message=error_message)

    # Charts
    script, div = group_chart(result)
    script_f, div_f = fair_chart(result, result_points)

    to_render = "eval.html"
    plain = False

    if "plain" in args:
        if args["plain"] == "True":
            plain = True
    if plain:
        to_render = "plain_eval.html"
    logger.debug("TYPES?: %s" % ut.get_persistent_id_type(item_id))
    if "data_test" in result:
        data_test = result["data_test"]
    else:
        data_test = None
    return render_template(
        to_render,
        item_id=ut.pid_to_url(item_id, ut.get_persistent_id_type(item_id)[0]),
        findable=result["findable"],
        accessible=result["accessible"],
        interoperable=result["interoperable"],
        reusable=result["reusable"],
        data_test=data_test,
        result_points=result_points,
        result_color=ut.get_color(result_points),
        script=script,
        div=div,
        script_f=script_f,
        div_f=div_f,
    )


@app.route("/es/export_pdf", endpoint="export_pdf_es")
@app.route("/en/export_pdf", endpoint="export_pdf_en")
def export_pdf():
    app.config["BABEL_TRANSLATION_DIRECTORIES"] = "translations"
    logging.debug(app.config["BABEL_TRANSLATION_DIRECTORIES"])
    babel.init_app(app, locale_selector=get_locale)
    try:
        args = request.args
        oai_base = None
        item_id = args["item_id"]
        logger.debug("ARGS_evaluator: %s" % args)
        sp = Smart_plugin(config["Repositories"])
        if config["local"]["only_local"] == "True":
            logger.debug("Only local TRUE")
            repo = config["local"]["repo"]
        elif "repo" not in args:
            plugin, url = sp.doi_flow(args["item_id"])
            repo = plugin
            oai_base = url
        else:
            logger.debug("Only local FALSE")
            repo = args["repo"]
        logger.debug("ITEM_ID: %s | REPO: %s" % (item_id, repo))
        result_points = 0
        num_of_tests = 41

        findable = {}
        accessible = {}
        interoperable = {}
        reusable = {}
        if oai_base is None:
            oai_base = repo_oai_base(repo)
        logger.debug("OAI_BASE: %s" % oai_base)

        try:
            if "oai_base" in args:
                if args["oai_base"] != "" and ut.check_url(
                    args["oai_base"] + "?verb=Identify"
                ):
                    oai_base = args["oai_base"]
                    logger.debug("Aqui OAI: %s" % oai_base)
            else:
                if ut.check_url(oai_base + "?verb=Identify") == False:
                    oai_base = ""
                    logger.debug("Aqui OAI: %s" % oai_base)
        except Exception as e:
            logger.error("Problem getting args")
        logger.debug("SESSION LANG: %s" % session.get("lang"))
        if repo is None or repo == "None":
            repo, oai_base = sp.doi_flow(item_id)
        body = json.dumps(
            {
                "id": item_id,
                "repo": repo,
                "oai_base": oai_base,
                "lang": session.get("lang"),
            }
        )
        logger.debug("BODY: %s" % body)
    except Exception as e:
        logger.error("Problem creating the object")
        logger.error(e)

    try:
        if os.path.exists("plugins/%s/translations" % repo):
            app.config["BABEL_TRANSLATION_DIRECTORIES"] = (
                "plugins/%s/translations" % repo
            )
            logging.debug(app.config["BABEL_TRANSLATION_DIRECTORIES"])
            babel.init_app(app, locale_selector=get_locale)
        url = "http://localhost:9090/v1.0/rda/rda_all"
        result = requests.post(
            url, data=body, headers={"Content-Type": "application/json"}
        )
        resultis = result.json()
        for key in resultis:
            result = resultis[key]
        result_points = 0
        weight_of_tests = 0
        for key in result:
            g_weight = 0
            g_points = 0
            for kk in result[key]:
                result[key][kk]["indicator"] = gettext(
                    "%s.indicator" % result[key][kk]["name"]
                )
                result[key][kk]["name_smart"] = gettext("%s" % result[key][kk]["name"])
                # pesos
                weight = result[key][kk]["score"]["weight"]
                weight_of_tests += weight
                g_weight += weight
                result_points += result[key][kk]["points"] * weight
                g_points += result[key][kk]["points"] * weight
            result[key].update(
                {
                    "result": {
                        "points": round((g_points / g_weight), 2),
                        "color": ut.get_color(round((g_points / g_weight), 2)),
                    }
                }
            )
            logger.debug(
                "%s has %f points and %s color"
                % (
                    key,
                    round((g_points / g_weight)),
                    ut.get_color(round((g_points / g_weight), 2)),
                )
            )

        result_points = round((result_points / weight_of_tests), 2)

        pdf_out = pdf_gen.create_pdf(
            result,
            "fair_report.pdf",
            ut.pid_to_url(item_id, ut.get_persistent_id_type(item_id)[0]),
            "static/img/logo_fair_eosc_2.png",
            "static/img/csic.png",
            result_points,
        )
        # pdf_output = pdfkit.from_file('fair_report.pdf','.')
        logger.debug("Tipo PDF")
        logger.debug(type(pdf_out))
        response = make_response(pdf_out)
        response.headers["Content-Disposition"] = "attachment; filename=fair_report.pdf"
        response.mimetype = "application/pdf"

        return response
    except Exception as e:
        logger.error("Problem parsing API result")
        logger.error(e)


def group_chart(result):
    data_groups = [
        pd.DataFrame.from_dict(result["findable"], orient="index"),
        pd.DataFrame.from_dict(result["accessible"], orient="index"),
        pd.DataFrame.from_dict(result["interoperable"], orient="index"),
        pd.DataFrame.from_dict(result["reusable"], orient="index"),
    ]

    figures = []
    types = ["Findable", "Accesible", "Interoperable", "Reusable", "FAIR"]
    i = 0

    for data in data_groups:
        data["value"] = 100 / len(data)
        data["angle"] = data["value"] / data["value"].sum() * 2 * pi
        data["color"] = status = pd.Series(data["points"]).apply(
            lambda x: (
                "#2ECC71"
                if x > 80
                else (
                    "#F4D03F"
                    if x >= 75
                    else "#F4D03F" if x >= 50 else "red" if x >= 0 else "#F4D03F"
                )
            )
        )
        data = data.sort_values(by=["points"], ascending=False)
        p = figure(
            title=types[i],
            toolbar_location=None,
            tools="hover",
            tooltips="@name_smart: @points",
            x_range=(-0.5, 0.5),
            sizing_mode="scale_width",
        )
        p.wedge(
            x=0,
            y=0,
            radius=0.4,
            start_angle=cumsum("angle", include_zero=True),
            end_angle=cumsum("angle"),
            line_color="white",
            fill_color="color",
            source=data,
        )
        p.axis.axis_label = None
        p.axis.visible = False
        p.grid.grid_line_color = None

        figures.append(p)
        i = i + 1
    script, div = components(row(figures))
    return script, div


def fair_chart(data_block, fair_points):
    types = ["Findable", "Accesible", "Interoperable", "Reusable", "FAIR"]
    # hay que poner a 0 algunos tests y perder sus nombres
    # o bien buscar otra forma de representarlo
    total = []
    total.append(data_block["findable"]["result"]["points"])
    total.append(data_block["accessible"]["result"]["points"])
    total.append(data_block["interoperable"]["result"]["points"])
    total.append(data_block["reusable"]["result"]["points"])
    total.append(fair_points)

    # Ajustamos una nueva columna status que contiene el color en funcion del score en el test
    status = pd.Series(total).apply(
        lambda x: (
            "#2ECC71"
            if x >= 75
            else "#F4D03F" if x >= 50 else "#E74C3C" if x >= 0 else "black"
        )
    )

    data = pd.DataFrame(
        {"types": types, "score": total, "status": status},
        columns=["types", "score", "status"],
    )

    p = figure(
        x_range=types,
        title="FAIR global scores",
        plot_height=250,
        sizing_mode="scale_width",
    )

    source = ColumnDataSource(dict(types=types, score=np.round(total, decimals=2)))

    labels = LabelSet(
        x="types",
        y="score",
        text="score",
        level="glyph",
        x_offset=-13.5,
        y_offset=0,
        source=source,
        render_mode="canvas",
    )

    p.vbar(x="types", top="score", width=0.9, color="status", source=data)

    p.xgrid.grid_line_color = None
    p.y_range.start = 0
    p.y_range.end = 105
    p.add_layout(labels)

    script, div = components(p)
    return script, div


def repo_oai_base(repo):
    if repo in config:
        if "oai_base" in config[repo]:
            return config[repo]["oai_base"]
        else:
            return ""
    else:
        return ""


class CheckIDForm(FlaskForm):
    item_id = StringField("ITEM ID", "")
    repo_dict = dict(config["Repositories"])
    repo = SelectField("REPO", choices=set(repo_dict))
    oai_base = StringField("(Optional) OAI-PMH Endpoint", "")


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
