#!/usr/bin/env python3
import configparser
from flask import Flask, render_template, request
import requests
from flask_wtf import FlaskForm
from wtforms import SelectField, TextField
import json

app = Flask(__name__)
app.config.update({
    'SECRET_KEY': 'sdafasfwefq3egthyjtyhwef',
    'TESTING': True,
    'DEBUG': True,
    'FLASK_DEBUG': 1
    })

config = configparser.ConfigParser()
config.read('./config.ini')


@app.route('/')
def index():
    form = CheckIDForm(request.form)
    return render_template('index.html', form=form)


@app.route('/evaluator', methods=['GET', 'POST'])
def evaluator():
    try:
        args = request.args
        form = CheckIDForm(request.form)
        item_id = args['item_id']
        repo = args['repo']

        result_points = 0
        num_of_tests = 41

        findable = {}
        accessible = {}
        interoperable = {}
        reusable = {}
        body = json.dumps({'id': item_id, 'repo': repo})
        if repo == 'oai-pmh':
            oai_base = args['oai_base']
            body = json.dumps({'id': item_id, 'repo': repo, 'oai_base': oai_base})
    except Exception as e:
        print("Problem creating the object")
        print(e)

    try:
        url = 'http://localhost:9090/v1.0/rda/rda_all'
        result = requests.post(url, data=body, headers={
                           'Content-Type': 'application/json'})
        print("=========================")
        print(result.json())
        print("=========================")
        result_points = 0
        num_of_tests = 0
        for key in result.json():
            for kk in result.json()[key]:
                num_of_tests += 1
                result_points += result.json()[key][kk]['points']

        result_points = round((result_points / num_of_tests), 2)
    except Exception as e:
        print("Problem parsing API result")
        if 'message' in result.json():
            error_message = "Exception: %s" % result.json()['message']
        else:
            error_message = "Exception: %s" % e
        return render_template('error.html', error_message=error_message)

    return render_template('eval.html', item_id=item_id,
                           findable=result.json()['findable'],
                           accessible=result.json()['accessible'],
                           interoperable=result.json()['interoperable'],
                           reusable=result.json()['reusable'],
                           result_points=result_points)


class CheckIDForm(FlaskForm):
    item_id = TextField(u'ITEM ID', '')
    repo_dict = dict(config['Repositories'])
    print(repo_dict)
    repo = SelectField(u'REPO', choices=repo_dict)
    oai_base = TextField(u'(Optional) OAI-PMH Endpoint', '')


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
