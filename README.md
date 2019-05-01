<h1 align="center">
  <a href="https://www.ndi.org/"><img src="https://www.ndi.org/sites/all/themes/ndi/images/NDI_logo_svg.svg" alt="NDI Logo" width="200"></a>
</h1>

<h1 align="center">
  Apollo
</h1>

  <p align="center">
    <a href="https://www.gnu.org/licenses/gpl-3.0.en.html">
      <img src="https://img.shields.io/badge/license-GPL-red.svg" alt="License"/>
    </a>
    <a href="https://www.python.org/">
      <img src="https://img.shields.io/badge/python-v2.7.15-blue.svg" alt="express"/>
    </a>
    <a href="https://docs.mongodb.com/">
      <img src="https://img.shields.io/badge/mongodb-v3.2-blue.svg" alt="express"/>
    </a>
    <a href="https://redis.io/">
      <img src="https://img.shields.io/badge/redis-v4.0-blue.svg" alt="express"/>
    </a>

   </p>
  

[![CircleCI](https://circleci.com/gh/nditech/apollo/tree/master.svg?style=svg&circle-token=d73aae2670476f167920a4494b6087a6f8ef49e9)](https://circleci.com/gh/nditech/apollo/tree/master)

  ### Table of Contents
  1. [Introduction](#introduction)
  1. [Install](#install)
  1. [Web Server Configuration](#nginx-configuration)
  1. [Logging In](#logging-in)


## Apollo 2.x Deployment Guide

### Introduction

This document details the steps required in deploying a fully functional installment of Apollo 2. Apollo is a data management platform to support citizen election observation and other large-scale structured data collection efforts. Developed by Tim Akinbo and his team at TimbaObjects in conjunction with NDI’s Elections team, Apollo aids the management of observers, verification of collected information, and automated aggregation for analysis. Citizen watchdogs play a critical role in validating political processes, but to be convincing must back claims with data. Elections are one of the foundations of legitimate democracy when the official results truly represent the will of the voters. Systematic election observation requires large amounts of structured information from hundreds or thousands of observers and determining what it means – fast. Apollo aids the management of observers, verification of collected information, and automated aggregation for analysis.

**Note that Apollo 2 is no longer being actively maintained.** Bugs and issues can be reported under the issues section for this repository, however NDI does not make any guarantees about actively addressing these.

### Install

#### Dependencies

The dependencies for building and deploying an Apollo 2 instance are:
* [Git](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git) - for retrieving the source code from a source code versioning repository
* [Docker](https://docs.docker.com/install/linux/docker-ce/ubuntu/) - for building and deploying the Apollo instance.
* [NGINX](https://www.nginx.com/resources/wiki/start/topics/tutorials/install/) - Apollo uses Nginx as a web-server for hosting the site.


#### Install and Build

After installing git, use the following commands to install the current version of Apollo from this repo and enter the directory. The current latest stable version of Apollo is v2.8.2 and is tagged accordingly. The command below will clone that version.

```
git clone https://github.com/nditech/apollo.git -b "v2.8.2"
cd apollo
```

Once the repository has been cloned, you build the application image by first changing the directory to the one containing the source code and running the command:

`sudo docker build -t apollo .`

This will start the build process where all application dependencies are downloaded and installed and an application image (from which the containers will be created) will be built. Apollo relies on an application container named 'apollo' by default - this houses the main web application and serves the application contents to the web browsers and processes all user input. In addition, supporting containers include database container (MongoDB) and the task queue container (Redis). 

Next, run the database and task queue containters:

```
sudo docker run -d --name database mongo:3.2
sudo docker run -d --name jobqueue redis:4.0
```

Next, we’ll want to create an environment configuration file for the Apollo instance. You can use the template at http://git.io/TAc4jg as a starting point and then edit as desired. To download the file, use:

```
wget -O ./.env http://git.io/TAc4jg
```

Now, launch the Apollo instance by linking the mongodb and redis containers:

```
sudo docker run -d --hostname apollo --name apollo --link jobqueue:redis --link database:mongodb -p 8000:5000 --env-file=.env apollo honcho start
```

### Nginx configuration

After deploying the containers, the Apollo application can be accessed by configuring Nginx. After installing Nginx on your server, become the root user. First, remove the default config files under `/etc/nginx/` using the following commands:

```
rm /etc/nginx/sites-enabled/default
rm /etc/nginx/sites-available/default
```

Then, download a copy of a sample apollo config file:

```
wget -O /etc/nginx/sites-available/apollo http://git.io/VCsVtw 
```

Then, create a symbolic link between the apollo config file in `sites-available` and `sites-enabled`, so that changes to one file or automatically made in the other.

```
ln -s /etc/nginx/sites-available/apollo /etc/nginx/sites-enabled/apollo
```

Make any necessary changes to the config file `sites-available/apollo` and then restart nginx using `service nginx restart` (or `service nginx start` if it has not yet been started).

### Logging in

You should now be able to get to your site by navigating to port `:8000` on your localhost or server (http://localhost:8000 or http://*server-ip-address*:8000). To log in, create a default user. To log in to the container, use `sudo docker exec –it apollo sh`, replacing apollo with the name of the main application docker container if it is named something else (to see the names of the running docker containers, use `sudo docker ps`). Once inside the container, run `./manage.py create_user`. You will be prompted to enter information for your account. Then, run `./manage.py add_userrole` and specify admin to give admin rights to your account.
