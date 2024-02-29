# How to use the Epos plugin of the FAIR evaluator 
To use the fair evalater you need access to a terminal 

## 1.Follow the steps indicated in the  documentation
https://github.com/EOSC-synergy/FAIR_eva/blob/main/docs/index.md which are executting the following commands

git clone https://github.com/EOSC-synergy/FAIR_eva.git
cd ./FAIR_eva
pip3 install -r requirements.txt
cp config.ini.template config.ini

Basically clone the github repo in your computer, change into de adecuate folder, install all the python modules necesary for the program  and copy the template for the configuration file 

## 2.Run fair.py (python3 fair.py)

Now you have the API running in that terminal (let's call it terminal 1) here you can see all the steps the API is following.


## 3.Make a request to evaluate  
On another terminal (terminal 2) you will make a curl request to that API. Here we will get the responses
In order to do that we use :
curl  -H  "accept: application/json"\
      -H  "Content-Type: application/json" \
      -d '{"id":"1b67c7f4-3cb8-473e-91a9-0191a1fa54a8","lang":"es","oai_base":  "https://www.ics-c.epos-eu.org/api/v1","repo":"epos"}'\
      -X POST "http://localhost:9090/v1.0/rda/rda_all"

It will return an evaluation of all the tests 
## DONE!

That one is a particular example there are two things you can change:
1.- The id to the one you are looking for 
2.- The end of the -X POST "http://localhost:9090/v1.0/rda/rda_all" you can change rda all for a code to another test.

If you are only interested in the scores and how your item qualifies in each category you can use fair-eva.py a simple script that writes the points in each category. This script is located in the scripts folder.
To use it you simply need to execute the command:

python3 scripts/fair-eva.py -ID 1b67c7f4-3cb8-473e-91a9-0191a1fa54a8 -R epos -B https://www.ics-c.epos-eu.org/api/v1 

Where in the -ID you put the UUID to evaluate, in -R the plugin  and in -B the endpoint.The ones in the example are from epos.

If are interested in the points in each test, just add --s True .
Then program will print all the tests scores




## How to obtain the UUID
The UUID is the id  that you need to access the metadata, there are two ways to obtain it: 

### 1. Conecting directly to the EPOS API

You can perform a curl to the EPOS API to get your UUID the process is the same as before 

curl -X 'GET' \
  'https://www.ics-c.epos-eu.org/api/v1/resources/search?q=SVO' \
  -H 'accept: application/json

Where the q (query) term is the text you are looking for. You will recieve a long response, the interesting part is at the bottom, it should look like:

               description": "The service allows to access data from the ground based C-band radar data located in Keflavik for Eyjafjallajokull eruption 2010, and data from both the C-band radar in Keflavik and a mobile X-band radar (50DX) by Kirkjubaejaklaustur for Grimsvotn eruption 2011.",
                "href": "https://www.ics-c.epos-eu.org/api/v1/resources/details?id=12b76f8e-d10e-4c5d-a113-4855f6bc3435",
                "id": "12b76f8e-d10e-4c5d-a113-4855f6bc3435",
                "status": 1,
                "title": "Ground based radar data Iceland",
                "uid": "www.epos-eu.org/epos-dcat-ap/Volcano_observations/Dataset/022/WSDistribution"
              }
            ],
            "name": "Ground-based remote sensing"
          }
        ],
        "name": "Volcano Observations"
      }
    ],
    "name": "domains"


The UUID is the "id" between "href" and "status". 
You may get more than one item, make sure you copy the UUID  of the one you are looking for 

An easy way to use the EPOS API is through the swagger UI https://www.ics-c.epos-eu.org/api/v1/ui/#/Resources%20Service/qstwbnlpzpxqswdrywpmifupoguizq, there you can use: get/resources/datasets in the Resources Service section 

### 2. Using the Fair_eva tool q parameter
In terminal 2:
Instead of using the previous comand use: 
curl  -H  "accept: application/json"\
      -H  "Content-Type: application/json" \
      -d '{"q":"SVO","id":"","lang":"es","oai_base":  "https://www.ics-c.epos-eu.org/api/v1","repo":"epos"}'\
      -X POST "http://localhost:9090/v1.0/rda/rda_f1_01m"

Same as before this is an example, you can change the q parameter to whatever you want to search. This will return the id of all the results found. To make sure its the one you are looking for you can make a curl to the API with the test  rda_f2_01m, this test looks at the findability of the metadata you are looking for, one of the elements it uses is the title, so use the curl:

curl  -H  "accept: application/json"\
      -H  "Content-Type: application/json" \
      -d '{"id":"1b67c7f4-3cb8-473e-91a9-0191a1fa54a8","lang":"es","oai_base":  "https://www.ics-c.epos-eu.org/api/v1","repo":"epos"}'\
      -X POST "http://localhost:9090/v1.0/rda/rda_f2_01m"


Now take a look at terminal 1, it will display a table with important findability related terms, one of them is the title so you can make sure the item is the one that you want (If the table displays a lot of ... items try to make th window wider and retry the test)

Another way to confirm the UUID is via the  EPOS API via the curl (get resources/details in swagger):

curl -X 'GET' \
  'https://www.ics-c.epos-eu.org/api/v1/resources/details?id=1b67c7f4-3cb8-473e-91a9-0191a1fa54a8' \
  -H 'accept: application/json'

After id= you should put the UUID you want to check 
