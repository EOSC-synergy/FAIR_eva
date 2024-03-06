# How to use the Epos plugin of the FAIR EVA 
To use the FAIR EVA you need access to a terminal 

## 1.Deply FAIR EVA
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

### An alternative way to use the FAIR eva
If you have access to SQAaaS, https://sqaaas.eosc-synergy.eu/ (you can get it through github) you can use the platform.

Once you have access click on the quality assesment and rewarding section, and go to the FAIR tab you will have to choose a tool.
Choose FAIR-EVA , then you will have to enter 3 values, the persistent identifier, the plugin (epos) and the endpoint (https://ics-c.epos-ip.org/development/k8s-epos-deploy/dt-geo/api/v1).

After that you have to clic in add tool and then start assesment.


## How to obtain the UUID
The UUID is the identifier that you need to access the metadata, there are two ways to obtain it: 

### 1. Conecting directly to the EPOS API

You can perform a curl to the EPOS API to get your UUID the process is the same as before 
````
curl -X 'GET' \
  'https://ics-c.epos-ip.org/development/k8s-epos-deploy/dt-geo/api/v1/resources/search?q=SVO' \
  -H 'accept: application/json'
````
Where the q (query) term is the text you are looking for. You will recieve a long response, the interesting part is at the bottom, it should look like:
````
{

  "filters": [
  
    {
      "children": [
        {
          "id": "dm9sY2FubyBtYWduaXR1ZGUvaW50ZW5zaXR5",
          "name": "volcano magnitude/intensity"
        },
        {
          "id": "dm9sY2FubyBvYnNlcnZhdG9yeQ==",
          "name": "volcano observatory"
        },
        {
          "id": "dm9sY2FubyBvY3VycmVuY2U=",
          "name": "volcano ocurrence"
        }
      ],
      "name": "keywords"
    },
    {
      "children": [
        {
          "id": "85e8de3b-747c-4ffa-8205-ed519b2669ed",
          "name": "Icelandic Meteorological Office"
        }
      ],
      "name": "organisations"
    },
    {
      "name": "sciencedomains"
    },
    {
      "name": "servicetypes"
    }
  ],
  "results": {
    "name": "domains"
  }
}

````

The UUID is the "id" in "children" juest before "name". 
You may get more than one item, make sure you copy the UUID  of the item you are looking for 



### 2. Using the FAIR EVA q parameter
In terminal 2:
Instead of using the previous comand use: 
````
curl  -H  "accept: application/json"\
      -H  "Content-Type: application/json"\
      -d '{"id":"7c9dfb3c-7db0-4424-8843-ada2143b00a0","lang":"es","oai_base":  "https://ics-c.epos-ip.org/development/k8s-epos-deploy/dt-geo/api/v1","repo":"epos"}' \
      -X POST "http://localhost:9090/v1.0/rda/rda_f2_01m"
````
Same as before this is an example, you can change the q parameter to whatever you want to search. This will return the id of all the results found. 
To make sure its the one you are looking for you can make a curl to the API with the test  rda_f2_01m, this test looks at the findability of the metadata you are looking for,
one of the elements it uses is the title.  

Now take a look at terminal 1, it will display a table with important findability related terms, one of them is the title so you can make sure the item is the one that you want
(If the table displays a lot of ... items try to make the window wider and retry the test)
