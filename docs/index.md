# FAIR EVA: Evaluator, Validator & Advisor

[![GitHub license](https://img.shields.io/github/license/indigo-dc/DEEPaaS.svg)](https://github.com/indigo-dc/DEEPaaS/blob/master/LICENSE)
[![Python versions](https://img.shields.io/pypi/pyversions/deepaas.svg)](https://pypi.python.org/pypi/deepaas)

FAIR EVA: Evaluator, Validator & Advisor has been developed to check the FAIRness level of digital objects from different repositories or data portals. It requires the object identifier (preferably persistent and unique identifier) and the repository to check. It also provides a generic and agnostic way to check digital objects.

## Description

FAIR EVA is a service that runs on the web. It can be deployed as a stand-alone application or in a docker container. It implements different web services: the API that manages the evaluation and the web interface to facilitate accessing and user-friendliness.

## Goals

The goals of this service are:

- Checks data and metadata from a digital object
- Based on some indicators, evaluates the FAIRness of the resource.
- Provides feedback to the users to improve

## Getting started

To launch the application in an stand-alone mode, the steps are the following:

```
git clone https://github.com/IFCA-Advanced-Computing/FAIR_eva.git
cd ./FAIR_eva
pip3 install -r requirements.txt
cp config.ini.template config.ini
/FAIR_eva/fair.py &
/FAIR_eva/web.py &
```

The last step, running web.py is optional if you don not want to deploy the web visual interface. The ports to run the app are 9090 for the API and 5000 for the web interface. They can be configured if needed.

### Example with fair.py 
To run the API in one  terminal just use 
```
python3 fair.py
```

In another terminal you can then use the following comand to ask the API for the information

```
curl -X POST "http://localhost:9090/v1.0/rda/rda_all" -H  "accept: application/json" -H  "Content-Type: application/json" -d '{"id":"http://hdl.handle.net/10261/157765","lang":"es","oai_base": "http://digital.csic.es/dspace-oai/request","repo":"oai-pmh"}'
```
The 'id' should be the DOI or handle of the document you want to check, and the 'oai_base' from the repository in which it can be found.

This one checks for everyone of the FAIR indicators and then gives and answer. For a list of all the options you can open your browser and go to http://localhost:9090/v1.0/ui/ to see the Swagger UI

### Docker version deployment

To deploy a docker container, just run the latest image:

```
docker run --name=fair_eva -p 9090:9090 -p 5000:5000 -dit --network host
```


## Architecture

FAIR evaluator implements a modular architecture to allow data services and repositories to develop new plugins to access its services. Also, some parameters can be configured like the metadata terms to check, controlled vocabularies, etc.

### Configuration

The config.ini file contains all the configuration parameters. They are distributed in different sections. To customize your FAIR evaluator deployment. It will work by default, but this is what you can edit:

```
[local]
# Defines if your service is deployed close to the data service and if it is only configured to work with that service
# only_local = true if it will run only for your service
only_local = false
repo = oai-pmh
```

The repositories or data portals that implements a plugin can be listed in the service. Ypu can configure those that you wants to appear in the list. Every repository should be shwon with the display name equal python Class name. The Generic class is "Evaluator"

```
[Repositories]
oai-pmh = 'Evaluator'
digital_csic = 'Digital.CSIC'
example_plugin = Example_Plugin
```

You can also customize the existing plugins to match with your user community. All the plugins are defined by a list of parameters like the following. The list of metadata terms to check identifiers, generic or disciplinar metadata, etc. need to match with the way you load the metadata from a resource.

In General, the format is ['metadata_schema', 'element', 'text_value', 'qualifier'], where:

- metadata_schema: The URL (like XSD) where the metadata schema is defined.
- element: Term of the metadata schema
- text_value: Value of the term
- qualifier: Subelement or sub-term that qualifies a type. It can also be the child of a given term.

For complex structures, an element can be something like Grandpa_term.parent_term.term. The way you load the metadat neet to take into accountot define the terms, subterms and qualifiers to check in the following configuration section.

```
[oai-pmh]
# Metadata terms to find the resource identifier
identifier_term = ['identifier']

# Metadata terms to check richness (generic). These terms should be included [term, qualifier]. None means no qualifier
terms_quali_generic = [['contributor',None],
                       ['date', None],
                       ['description', None],
                       ['identifier', None],
                       ['publisher', None],
                       ['rights', None],
                       ['title', None],
                       ['subject', None]]

# Metadata terms to check richness (disciplinar). These terms should be included [term, qualifier]
terms_quali_disciplinar = [['contributor', None],
                           ['date', None],
                           ['description', None],
                           ['identifier', None],
                           ['publisher', None],
                           ['rights', None],
                           ['title', None],
                           ['subject', None]]

# Metadata terms that defines accessibility
terms_access = [['access', ''], ['rights', '']]

# Metadata terms wich includes controlled vocabularies. More controlled vocabularies can be imlpemented in plugins
terms_cv = [['coverage', 'spatial'], ['subject', 'lcsh']]

# List of data formats that are standard for the community
supported_data_formats = [".txt", ".pdf", ".csv", ".nc", ".doc", ".xls", ".zip", ".rar", ".tar", ".png", ".jpg"]

# Metadata terms that defines links or relation with authors, contributors (preferebly in ORCID format)
terms_qualified_references = ['contributor']

# Metadata terms that defines links or relation with other resources, (preferebly in ORCID format, URIs or persistent identifiers)
terms_relations = ['relation']

# Metadata terms that defines the license type
terms_license = [['license', '', '']]
```

### Develop your own plugin

If you want to custimze the access to your resources (data and metadata) or your data service/repository, you can develop your own plugin. Just follow the next steps:

- Copy the /plugins/example_plugin folder and name it with the name of your plugin
- Redefine the `get_metadata(self)` function to collect the metadata from your portal or repository.
- Indicate the protocol for accessing (meta)data.
- By default, the tests for the different indicators are extended from the parent class Evaluator. Please, check if those tests suit your case.
- We recommend checking the following tests. Take into account that some of the tests on the generic plugin use the OAI-PMH protocol, so, if you don’t have such as protocol, you need to redefine.
- If your identifier is not an universal or unique one but you want to perform more tests (internal IDs): rda_f1_01m(self), rda_f1_02m(self), rda_a1_01m, rda_a1_02m, rda_a1_03m, rda_a1_03d, rda_i1_01d,
- Rda_f2_01m_generic: checks terms from your metadata standard referent.
- Rda_a1_01m: checks how the data is accessed.
- rda_i1_01d: checks standard formats for data representation within your community.
- Any other with community specifications
- In config.ini, within your plugin folder, add the following information:

```
[example_plugin]
# In [Repositories] add the new plugin name (without .py) equal the name of the class. E.g: example_plugin = 'Example_Plugin'
# Create new section (e.g. [example_plugin]) to add any necessary config info. For example, if your system have OAI-PMH endpoint, you can add a oai_base attribute.
# Metadata terms to find the resource identifier
identifier_term = ['identifier']
# ETC
```

In api/rda.py import the api.example_plugin.
(This will not be necesary in the next release). Edit api/rda.py to add this type of repo object in def repo_object(body), add:

```
elif repo == "example_plugin":
eva = Example_Plugin(item_id, lang)
```

#### Translations

Babel or pybabel is used to automatically translate the feedback messages. If you want to edit any of those messages or add a new language, please modify/add the `*.po` files under translations folder and execute this command:
`pybabel compile -f -d .`

## Evaluation tests

### RDA Indicators

[Indicators](indicators.md)

### Technical implementation

[Technical implementation](technical_implementation.md)
