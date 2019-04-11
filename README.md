<h1 align="center">
  <a href="https://www.ndi.org/"><img src="https://www.ndi.org/sites/all/themes/ndi/images/NDI_logo_svg.svg" alt="NDI Logo" width="200"></a>
</h1>

<h1 align="center">
  Apollo
</h1>

[![CircleCI](https://circleci.com/gh/nditech/dev-elections/tree/master.svg?style=svg&circle-token=d73aae2670476f167920a4494b6087a6f8ef49e9)](https://circleci.com/gh/nditech/dev-elections/tree/master)

## Apollo 3.x Deployment Guide

#### Introduction

This document details the steps required in deploying a fully functional installment of Apollo 3. As compared to its previous version, Apollo 3 has improved the steps required in getting an installation up.

#### Dependencies

The only dependencies for building and deploying an Apollo 3 instance are git - for retrieving the source code from a source code versioning repository and docker for building and deploying the Apollo 3 instance.

Documentation on how to install git may be found here while you could find out about docker here.

#### Obtaining the Source

After installing git, you would be able to clone the current version of Apollo from this repo, https://github.com/nditech/dev-elections. Due to the fact this repository is private, it would require that you upload a deployment SSH key to clone to a regular server or use an authenticated URL (if you have an account on GitHub that has access to the repository). You will find the section for adding deployment keys to the repository here: https://github.com/nditech/dev-elections/settings/keys.

After downloading, configure a settings file in the main folder called `settings.ini`. The install will not work if a settings file is not created with a Secret Key specified. The secret key can be any randomly generated string of characters. A basic sample settings file is shown below. For more information on additional setting configurations, read the section "Application Configuration Settings" below.

```
[settings]
SECRET_KEY=sD2av35FAg43rfsDa
SSL_REQUIRED=False
```

### Installation: Using Docker Compose

In order to simplify the deployment process, Apollo now includes a docker compose application configuration to allow admins skip the entire process of having to start each of the database, task queue, worker and main application containers individually.

Docker compose is an optional dependency and you will find instructions on how to install it here.

To start the application, simply run:

docker-compose up -d

(Alternatively, if after running docker-compose, changes are made and a clean install is needed that builds the containers from scratch without drawing upon the cached images, use `docker run build --no-cache`) 

The main application container and worker containers will be built and run together with the supporting database and task queue containers.


### Nginx configuration

Apollo is designed to work with an Nginx webserver. After installing nginx on your server, go to `/etc/nginx/`. Remove all files from the directories `sites-available` and `sites-enabled`. Create a blank file called `apollo` in `sites-available`, and create a symbolic link to a file in `sites-enabled` by running the command below.

`ln -s /etc/nginx/sites-available/apollo /etc/nginx/sites-enabled/apollo`

Then edit the apollo file in `sites-available` with Nginx configurations. A sample file is shown below, with **insert site url** indicating places in which the site url should be substituted in.

```
server {
    listen 80;
    server_name **insert site url**;
    location / {
        rewrite ^ https://$server_name$request_uri? permanent;
    }
}

server {
    listen 443;
    server_name **insert site url**;
    #limit_req zone=one burst=10 nodelay;
    #limit_req_status 429;
    ssl_trusted_certificate /etc/ssl/certs/demcloud_combined.crt;

    location / {
        proxy_pass http://localhost:5000;
        proxy_redirect http:// $scheme://;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Server $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        port_in_redirect off;
        proxy_connect_timeout 300;
        proxy_read_timeout 180;
    }
```

You should now be able to login to your site by navigating to port `:5000` on your localhost or server. The default login is username/password: `admin`/`admin`.

### Application Configuration Settings

Each deployment installation can be further customized by modifying the contents of the settings.ini file. Here are a collection of settings parameters and sample values together with an explanation of what they do.

SECRET_KEY
(e.g. LBZyd8EY80mALqb7bl8o3da8)

The secret key contains a random string of characters, numbers and symbols and is used internally for signing and encrypting cookies and other security-related tokens. Best security practice requires that you set the value to a random value before starting the containers. Note that if this value is changed after the application is already fully configured, then user logins will stop working as the application would not be able to decrypt stored passwords. So this should remain the same throughout the lifetime of the application. This is a compulsory configuration option.


SSL_REQUIRED
(e.g. False)

This parameter determines whether the application server will explicitly check if all requests are being served over a secure (https) connection. By setting this value to True, you effectively turn this check on and all connections must be secure before access is granted.


TIMEZONE
(e.g. Africa/Lagos)

The timezone parameter configures the timezone that the application server uses by default. Usually this is set to the timezone of the country for which the application instance is deployed. For a full list of support timezone values, please visit this wikipedia article.


#### GOOGLE_TAG_MANAGER (REQUIRED)
(e.g. GTM-1234567)

If you need to manage tags that are inserted into the application, one way to do so it to use the Google Tag Manager. This parameter allows you to set the Google Tag Manager code that is linked to the Google account from where the tags will be managed.


REDIS_DATABASE
(e.g. 0)

This value determines the redis database that is used by the application. It takes the default value of 0 but (in the unlikely event that you need to share a redis installation) it can be changed to a different value. By default most redis installations have a maximum value of 15.


REDIS_HOSTNAME
(e.g. redis)

As was described above, if you require connecting to an external redis server, you can specify the value of the hostname for this redis database here.


DATABASE_HOSTNAME
(e.g. postgres)

As was the case in REDIS_HOSTNAME, there might be cases where an external PostgreSQL database is to be used, setting the DATABASE_HOSTNAME allows the application and worker applications to connect to this.



DATABASE_NAME
(e.g. apollo)

If you need to use the non-default database name for the installation, you can change the value here. Please note that if you are using an external PostgreSQL server, you may not need to create and link to the postgres container; in which case, simply providing the DATABASE_HOSTNAME and the DATABASE_NAME will be sufficient for the application containers to connect to the provided database.

You would also need to drop the DATABASE_NAME environment specification (-e DATABASE_NAME=...) when creating the application containers.


DEBUG
(e.g. False)

Debug information is usually only used when the application is being built or when an issue is being debugged. The default value of False is sufficient and should only be changed to True if there’s the need to debug the application. Setting DEBUG to True may reveal sensitive information to the user and should only be used when actual debugging is being done and reverted to the default value when debugging is over.

MAIL_SERVER
(e.g. smtp.sendgrid.net)
MAIL_PORT
(e.g. 587)
MAIL_USE_TLS
(e.g. True)
MAIL_USERNAME
(e.g. sendgrid-username)
MAIL_PASSWORD
(e.g sendgrid-apikey)

These set of configuration values allow the administrator to configure a mail server for the purpose of being able to send out transactional emails like password resets, notices on task completion, etc. It is highly recommended that these values are configured.


PROMETHEUS_SECRET
(e.g. pmsecretz)

Apollo 3 provides support for an external monitoring server (Prometheus) to be able to obtain application performance metrics. In order to randomize the URL from which the stats are retrieved from, the PROMETHEUS_SECRET is added as an additional URL fragment and must be correct for the metrics to be provided. The metrics url becomes https://apollo3servername/metrics/{PROMETHEUS_SECRET}.


### Analytics Tracking
For digital marketing or product improvement initiatives you may want to include JavaScript and or HTML snippet tags for tracking and analytics on Apollo. 

Apollo leverages Google Tag Manager to achieve this. To enable Tag Manager, modify the `settings-docker.ini` file located in the project root directory. 
Next, add the configuration parameter `GOOGLE_TAG_MANAGER_KEY` and specify the **tag manager key** you get from Google and restart the container.

For more information on using Google Tag Manager [see the following resource](https://marketingplatform.google.com/about/tag-manager/).



### Alternative Installation Method: Without Docker-Compose ###

An older installation method is documented below. In almost all cases, using docker compose is preferable. However if for some reason this is not possible, use the method below instead in place of the section above labeled *Installation: Using Docker Compose*.

#### Building the Docker Images 

Once the repository has been cloned, you build the application image by first changing the directory to the one containing the source code and running the command:

docker build -t apollo .

This will start the build process where all application dependencies are downloaded and installed and an application image (from which the containers will be created) will be built.
Running the Application Containers

There are two essential application containers that are required in every Apollo 3 deployment. The first one is the application container - this houses the main web application and serves the application contents to the web browsers and processes all user input.

The second is the long-running task worker and is responsible for handling tasks that take a much longer time to run and that may otherwise block the main web application process and possibly timeout while waiting for the task to complete.

Supporting containers include database container (PostgreSQL) and the task queue container (Redis).

Start out by first running the database and task queue containers:

docker run -d -e POSTGRES_DB=${DATABASE_NAME:-apollo} -v postgres_data:/var/lib/postgresql/data -n postgres postgres:10-alpine
docker run -d -n redis redis:4-alpine 

Then you run the worker container:

docker run -d -n worker --link postgres --link redis -e DATABASE_NAME=${DATABASE_NAME:-apollo} -v upload_data:/app/uploads -v settings.ini:/app/settings.ini apollo:latest pipenv run ./manage.py worker

Finally, you can then run the main application container:

docker run -d -n web --link postgres --link redis -e DATABASE_NAME=${DATABASE_NAME:-apollo} -v upload_data:/app/uploads -v ./settings.ini:/app/settings.ini apollo:latest pipenv run ./manage.py gunicorn -c gunicorn.conf

In both instances, the database (PostgreSQL) and task queue (Redis) containers are linked to the worker and main application containers.
