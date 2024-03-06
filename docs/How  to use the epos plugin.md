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
