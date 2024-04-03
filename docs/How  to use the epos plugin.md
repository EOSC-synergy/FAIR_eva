# How to use the Epos plugin of the FAIR EVA
To use the FAIR EVA you need access to a terminal

## Quick start

### 1. Deploy FAIR EVA
Following the steps in the [documentation](https://github.com/EOSC-synergy/FAIR_eva/blob/main/docs/index.md):
```
git clone https://github.com/EOSC-synergy/FAIR_eva.git
cd ./FAIR_eva
pip3 install -r requirements.txt
cp config.ini.template config.ini
```
Basically clone the github repo on your computer, change into the adequate folder, install all the python modules necessary for the program  and copy the template for the configuration file

### 2. Run FAIR EVA API
The FAIR EVA API needs to running in the background or in an individual terminal. We will follow the latter approach for this demo:
```
(terminal #1) python3 fair.py
```

### 3. Test FAIR EVA
For the sake of simplificity, we will use the metadata identifier `7c9dfb3c-7db0-4424-8843-ada2143b00a0` that exists in the current [DT-GEO prototype](https://ics-c.epos-ip.org/development/k8s-epos-deploy/dt-geo/api/v1). FAIR EVA comes with a CLI that simplies the task of making requests to the API. We will use it in a different terminal (terminal #2) from the one that launched the API in the previous step:

```
(terminal #2) python3 scripts/fair-eva.py --id 7c9dfb3c-7db0-4424-8843-ada2143b00a0 --plugin epos --repository https://ics-c.epos-ip.org/development/k8s-epos-deploy/dt-geo/api/v1
```

The previous command is similar to the following `curl` command:

```
(terminal #2) curl  -H  "accept: application/json"\
      -H  "Content-Type: application/json" \
      -d '{"id":"7c9dfb3c-7db0-4424-8843-ada2143b00a0","lang":"es","oai_base": "https://ics-c.epos-ip.org/development/k8s-epos-deploy/dt-geo/api/v1","repo":"epos"}'\
      -X POST "http://localhost:9090/v1.0/rda/rda_all"
```

In both cases the evaluation of all the tests will be returned.

## Customize your request

### How to obtain the UUID
The UUID is the identifier that you need to access the metadata. There are two ways to obtain it:

#### 1. Using the FAIR EVA q parameter
In terminal 2, instead of using the previous comand use:
```
(terminal #2) curl  -H  "accept: application/json"\
      -H  "Content-Type: application/json"\
      -d '{"id":"7c9dfb3c-7db0-4424-8843-ada2143b00a0","lang":"es","oai_base":  "https://ics-c.epos-ip.org/development/k8s-epos-deploy/dt-geo/api/v1","repo":"epos"}' \
      -X POST "http://localhost:9090/v1.0/rda/rda_f2_01m"
```
Same as before this is an example, you can change the q parameter to whatever you want to search. This will return the id of all the results found.
To make sure its the one you are looking for you can make a curl to the API with the test  rda_f2_01m, this test looks at the findability of the metadata you are looking for. One of the elements it uses is the title.

Now take a look at terminal 1, it will display a table with important findability-related terms, one of them is the title, so you can make sure the item is the one that you want,
(If the table displays a lot of ... items try to make the window wider and retry the test)


#### 2. Connecting directly to the EPOS API

You can perform a curl to the EPOS API to get your UUID. Yhe process is the same as before
```
curl -X 'GET' \
  'https://ics-c.epos-ip.org/development/k8s-epos-deploy/dt-geo/api/v1/resources/search?q=SVO' \
  -H 'accept: application/json'
```
Where the q (query) term is the text you are looking for. You will receive a long response. The interesting part is at the bottom; it should look like:
```
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
```

The UUID is the "id" in "children" just before "name".
You may get more than one item, make sure you copy the UUID  of the item you are looking for.

### Running a single FAIR check

The API path can be modified in order to trigger the evaluation of a single FAIR check. This is done through the `--api-endpoint` option as follows:

```
python3 scripts/fair-eva.py --id 7c9dfb3c-7db0-4424-8843-ada2143b00a0 --plugin epos --repository https://ics-c.epos-ip.org/development/k8s-epos-deploy/dt-geo/api/v1 --api-endpoint http://localhost:9090/v1.0/rda/rda_f1_01m
```

This command will return the evaluation of the RDA-F1-01M indicator.

### Scores
To get a clear view of the scores the CLI has 2 extra parameters that print the punctuation of the item in the distict catergories.

You can add -s to get the points in each of the FAIR catergories and the total score.
```
(terminal #2) python3 scripts/fair-eva.py --id 7c9dfb3c-7db0-4424-8843-ada2143b00a0 --plugin epos --repository https://ics-c.epos-ip.org/development/k8s-epos-deploy/dt-geo/api/v1 -s
```
Or you can add -fs to get the points in each of the different checks
 the total score.
```
(terminal #2) python3 scripts/fair-eva.py --id 7c9dfb3c-7db0-4424-8843-ada2143b00a0 --plugin epos --repository https://ics-c.epos-ip.org/development/k8s-epos-deploy/dt-geo/api/v1 -fs
```
You can also use them both together. Note that the points are not the basic average of the tests, because each test has a different weight.

### Configuration through config.ini.
There are some tests whose results depend on things outside of the metadata given by the EPOS API so their result depends on a configuration parameter. These parameters are stored in the file 'config.ini' you can change these parameters to change some results. WARNING a lot of parameters are essential for the tool to work. If the parameter you are interested in changing doesn't appear on the following list you probably shouldn't change it:

1. supportted_data_formats: The formats that are considered standard.
2. terms_access_protocols: The list of accepted protocols to access (meta)data.
3. metadata_access_manual: a guide on how to access the metadata manually without the tool.
4. data_access_manual: A guide on how to access data manually
5. terms data model*: The model of the data you are checking
6. metadata_standard: The standard in which the metadata is based on
7. metadata_persistance*: This is the policy of the persistence of the metadata.
8. metadata_authentication*: The authentication or autorisation protocols provided by the platform
9. [fairsharing]username and password: If you want to refresh the fairsharing list, you can use your fairsharing username and password

There are some parameters with * this mean that at the time of writing we have not found (mainly becaiuse it doesn't exist at the moment or is not clear) a good value.
## Alternative ways to use the FAIR EVA
There are two alternatives if you do not want to install FAIR EVA.

### Web portal: SQAaaS platform

If you have access to [SQAaaS](https://sqaaas.eosc-synergy.eu/), (you can get it through github) you can use FAIR EVA through the platform.

Once you have access, click on the quality assessment and rewarding section, and go to the FAIR tab, you will have to choose a tool.
Choose FAIR-EVA, then you will have to enter 3 values: the persistent identifier, the plugin (epos) and the [DT-GEO endpoint](https://ics-c.epos-ip.org/development/k8s-epos-deploy/dt-geo/api/v1).

After that, you have to click on "add tool" and then start the assessment.

### Docker
If you have docker installed you can build the dockerfile in the repository. To do that, download the dockerfile on your computer and then just type the command:

```
docker build . -t fair
```

This will build the image in your Dockerfile. Then you have to run it.

```
docker run  --network host -d fair
```

Once it is running, it will act the same way as terminal 1. If you want to see its contents use

```
docker logs <dockerID>
```

To get the docker id just execute.

```
docker ps
```

The way to comunicate with the Docker container is the same as the one explained before, you can use `fair-eva.py` or `curl` commands.
