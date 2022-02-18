[![codecov](https://codecov.io/gh/MolSSI/qikpropservice/branch/master/graph/badge.svg)](https://codecov.io/gh/MolSSI/qikpropservice)

MolSSI QikProp As A Service
===========================

A repository for serving QikProp v3 as a webservice and API access point.
 
This version of QikProp has been provided by [William L. Jorgensen](http://zarbi.chem.yale.edu) and hosted as
a service by the [Molecular Sciences Software Institute (MolSSI)](https://molssi.org/). To report a
problem or suggest improvements, please open an issue on
[the Project GitHub](https://github.com/MolSSI/qikpropservice). Additional features and options will be
added over time.

There are two main components for this project:
* A web application where data can be uploaded in the form, and provides the endpoint for the API
* A standalone API wrapper for CLI calls to the service hosted through the web app

How to run and use the Web App for development
==============================================

The web app exists in the `webapp` folder of this repository.

### 1- Install Python requirements:

Run in shell, create python env, and install requirements:

```bash
conda create -n qikpropservice 
conda activate qikpropservice
pip install -r requirements.txt
```


### 2- Install JavaScript requirements:

Next, install Node (front-end), and install JS requirements, 
which will be fetched from package.json automatically. In Ubuntu:

```bash
sudo apt-get install nodejs
cd webapp/app/static
npm install
```

### 3- Database setup

1. Install mongodb based on your operating system from 
https://docs.mongodb.com/guides/server/install/

2. Create a `webapp/.env` file, and add your DB URI to the config file:
```.env
MONGO_URI='mongodb://usr_username:user_password@localhost:27017/qikpropservice_db'
```

Replace `user_username` and `user_password` with your own values from your installation. 
You **don't** have to create a database after your install mongodb because the application will do
 it later.


Note: In the future when you need to, add PUBLICLY shared environment attributes to `.flaskenv` file, with key values that will be exported to the environment (dev, prod, etc).
Use `.env` file for private variables that won't be shared or pushed to Github. Note that `.env` overrides `.flaskenv`, and both override `config.py`.



### 4- Run the local server

To run the website locally, use: 

```bash
flask run
```


## To Use Docker Compose (instead of the above steps):

Run docker-compose directly, or optionally, change any desired environment variables by creating 
a `.env` file which will be read automatically by docker-compose.

** It is very important to make sure that the shared folder has the right user NOT root owner. **

```bash
# create the host volume folder with non-root access
mkdir docker_data
chown -R myUser:myUse docker_data
# clean unused docker images and containers
./dockerclean.sh
# build and run containers
docker-compose up --build 
```

## More resources:

1. For Docker deployment config example, check this
https://www.digitalocean.com/community/tutorials/how-to-set-up-flask-with-mongodb-and-docker

2. A service file has been included for getting this running as a service. See this url for more details
https://community.hetzner.com/tutorials/docker-compose-as-systemd-service 
