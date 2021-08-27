#!/usr/bin/env python3
import configparser
from flask import Flask, render_template, request, redirect, url_for, session, g
from flask_babel import Babel, lazy_gettext as _l
import logging
import requests
import api.utils as ut
from flask_wtf import FlaskForm
from wtforms import SelectField, TextField
import json
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

app = Flask(__name__)
app.config.update({
  'SECRET_KEY': 'sdafasfwefq3egthyjtyhwef',
  'TESTING': True,
  'DEBUG': True,
  'FLASK_DEBUG': 1,
  'PATHS': [
    'about_us',
    'evaluator'
  ],
  'BABEL_DEFAULT_LOCALE': 'es',
  'BABEL_LOCALES': [
    'en',
    'en-CA',
    'en-IE',
    'en-GB',
    'en-US',
    'es',
    'es-ES',
    'es-MX'
  ]
})
babel = Babel(app)
IMG_FOLDER = '/static/img/'

config = configparser.ConfigParser()
config.read('./config.ini')

@app.before_request
def get_global_language():
  g.babel = babel
  g.language = get_locale()


@babel.localeselector
def get_locale():
  lang = request.path[1:].split('/', 1)[0]

  if lang in app.config['BABEL_LOCALES']:
    session['lang'] = lang
    return lang

  if (lang_in_session()):
    return session.get('lang')

  default_lang = fallback_lang()
  session['lang'] = default_lang
  return default_lang


def lang_in_session():
  return (
    session.get('lang') is not None and
    session.get('lang') in app.config['BABEL_LOCALES']
  )


def fallback_lang():
  best_match = request.accept_languages.best_match(app.config['BABEL_LOCALES'])

  if best_match is None:
    return app.config['BABEL_DEFAULT_LOCALE']

  if 'en' in best_match:
    return 'en'

  return 'es'


@app.route('/', defaults={'path': ''}, methods=['GET','POST'])
@app.route('/<path:path>', methods=['GET','POST'])
def catch_all(path):
  if path == '':
    return redirect(url_for('home_'+g.language))
  subpaths = path.split('/')
  if len(subpaths) > 2:
    subpaths.pop(0)
  if subpaths[0] in app.config['BABEL_LOCALES']:
    if len(subpaths) > 1:
      if subpaths[1] in app.config['PATHS']:
        return redirect(url_for(subpaths[1]+'_'+subpaths[0], **request.args))
      else:
        return redirect(url_for('not-found_'+subpaths[0]))
    else:
      return redirect(url_for('home_'+subpaths[0]))
  else:
    if subpaths[0] in app.config['PATHS']:
      return redirect(url_for(subpaths[0]+'_'+g.language, **request.args))
    else:
      if len(subpaths) > 1:
        if subpaths[1] in app.config['PATHS']:
          return redirect(url_for(subpaths[1]+'_'+g.language, **request.args))
      else:
        return redirect(url_for('not-found_'+g.language))

@app.route("/es", endpoint="home_es")
@app.route("/en", endpoint="home_en")
def index():
    form = CheckIDForm(request.form)
    return render_template('index.html', form=form)

@app.route("/es/not-found", endpoint="not-found_es")
@app.route("/en/not-found", endpoint="not-found_en")
def not_found():
  return render_template('not-found.html')

@app.route("/es/about_us", endpoint="about_us_es")
@app.route("/en/about_us", endpoint="about_us_en")
def about_us():
    return render_template('about_us.html')

@app.route("/es/evaluator", endpoint="evaluator_es", methods=['GET', 'POST'])
@app.route("/en/evaluator", endpoint="evaluator_en", methods=['GET', 'POST'])
def evaluator():
    try:
        args = request.args
        #form = CheckIDForm(request.form)
        for e in args:
            logging.debug("MIAU: %s" % e)
        item_id = args['item_id']
        repo = args['repo']
       
        logging.debug("ITEM_ID: %s | REPO: %s" % (item_id, repo))
        result_points = 0
        num_of_tests = 41

        findable = {}
        accessible = {}
        interoperable = {}
        reusable = {}
        if args['oai_base'] is not None:
            oai_base = args['oai_base']
        else:
            oai_base = None
        logging.debug("SESSION LANG: %s" % session.get('lang'))
        body = json.dumps({'id': item_id, 'repo': repo, 'oai_base': oai_base, 'lang': session.get('lang')})
    except Exception as e:
        logging.error("Problem creating the object")
        logging.error(e)

    try:
        url = 'http://localhost:9090/v1.0/rda/rda_all'
        result = requests.post(url, data=body, headers={
                           'Content-Type': 'application/json'})
        result = result.json()
        result_points = 0
        weight_of_tests = 0
        for key in result:
            g_weight = 0
            g_points = 0
            for kk in result[key]:
                weight = result[key][kk]['score']['weight']
                weight_of_tests += weight
                g_weight += weight
                result_points += result[key][kk]['points'] * weight
                g_points += result[key][kk]['points'] * weight
            result[key].update({'result': {'points': round((g_points / g_weight), 2),
                'color': ut.get_color(round((g_points / g_weight), 2))}})
            logging.debug("%s has %f points and %s color" % (key, round((g_points / g_weight)), ut.get_color(round((g_points / g_weight), 2))))

        result_points = round((result_points / weight_of_tests), 2)
    except Exception as e:
        logging.error("Problem parsing API result")
        if 'message' in result:
            error_message = "Exception: %s" % result['message']
        else:
            error_message = "Exception: %s" % e
        return render_template('error.html', error_message=error_message)

    logging.debug("==========================")
    logging.debug(result)
    logging.debug("==========================")
    return render_template('eval.html', item_id=item_id,
                           findable=result['findable'],
                           accessible=result['accessible'],
                           interoperable=result['interoperable'],
                           reusable=result['reusable'],
                           result_points=result_points)


class CheckIDForm(FlaskForm):
    item_id = TextField(u'ITEM ID', '')
    repo_dict = dict(config['Repositories'])
    repo = SelectField(u'REPO', choices=repo_dict)
    oai_base = TextField(u'(Optional) OAI-PMH Endpoint', '')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
