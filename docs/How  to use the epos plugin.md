# How to use the Epos plugin of the FAIR EVA 
To use the FAIR EVA you need access to a terminal 

## 1.Deploy FAIR EVA
Follow the steps in th edocumentation:[Documentation](https://github.com/EOSC-synergy/FAIR_eva/blob/main/docs/index.md) 

Those steps  are executting the following commands
```
git clone https://github.com/EOSC-synergy/FAIR_eva.git
cd ./FAIR_eva
pip3 install -r requirements.txt
cp config.ini.template config.ini
```

Basically clone the github repo in your computer, change into de adequate folder, install all the python modules necesary for the program  and copy the template for the configuration file 

## 2.Run FAIR EVA API
```
python3 fair.py
```
Now you have the API running in that terminal (let's call it terminal 1) here you can see all the steps the API is following.


## 3.Test FAIR EVA  
On another terminal (terminal 2) you will make a curl request to that API. Here we will get the responses
In order to do that we use :
```
curl  -H  "accept: application/json"\
      -H  "Content-Type: application/json" \
      -d '{"id":"7c9dfb3c-7db0-4424-8843-ada2143b00a0","lang":"es","oai_base":  "https://ics-c.epos-ip.org/development/k8s-epos-deploy/dt-geo/api/v1","repo":"epos"}'\
      -X POST "http://localhost:9090/v1.0/rda/rda_all"
```
It will return an evaluation of all the tests 
## Customise your request.

You can change:
1. The id to the one you are looking for 
2. The end of the -X POST == "API path" you can change rda all for a code to another test. For example you can look only for the test f1_01m via http://localhost:9090/v1.0/rda/rda_f1_01m

A simple way to calculate the scores and how your item qualifies in each category is fair-eva.py a simple script that writes the points in each category.
This script is located in the scripts folder.
To use it you simply need to execute the command (you still need terminal 1 open with the API running):
```
python3 scripts/fair-eva.py --id 7c9dfb3c-7db0-4424-8843-ada2143b00a0 --plugin epos --repository https://ics-c.epos-ip.org/development/k8s-epos-deploy/dt-geo/api/v1 
```
documentation on the script:  
```
usage: fair-eva.py [-h] [-i IDENTIFIER] [-p PLUGIN] [-r URL] [-s]
                   [--api-endpoint URL] [-fs]
                   
Command-line interface for FAIR EVA tool
options:

  -h, --help            show this help message and exit

  -i IDENTIFIER, --id IDENTIFIER
                        Identifier of the (meta)data

  -p PLUGIN, --plugin PLUGIN
                        FAIR EVA plugin name

  -r URL, --repository URL
                        (meta)data repository endpoint

  -s, --scores

  --api-endpoint URL    Enpoint to perform HTTP request. Example:
                        http://localhost:9090/v1.0/rda/rda_all

  -fs, --full-scores
````
