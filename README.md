## Apollo ##

[![CircleCI](https://circleci.com/gh/nditech/dev-elections/tree/master.svg?style=svg&circle-token=d73aae2670476f167920a4494b6087a6f8ef49e9)](https://circleci.com/gh/nditech/dev-elections/tree/master)

Apollo is an election monitoring platform that is designed to use the Parallel Voting Tabulation methodology of election monitoring to collect, store and analyse election data. This data is submitted by election observers using text messaging and provides tools to enable data managers and clerks manage the collected data. Apollo is capable of validating collected data and providing user-friendly error reports to enable election observers self-correct and resend their information.

#### Installation ####

##### Depedencies #####
Apollo requires only **docker** and **git** to be installed on the host.

##### Build Instructions #####
```
git clone git@github.com:nditech/dev-elections.git
cd dev-elections
docker build -t apollo:latest .
```

##### Deployment #####
First create docker volumes for the database data and for storing uploaded files
```
docker volume create database_data
docker volume create upload_data
```

Next choose a password for the PostgreSQL server and start containers for Redis and PostgreSQL (in this example, the chosen password is *iJqHvUqA923TPIkPHKURkXV4*)
``` 
docker run -d --name redis redis:4-alpine
docker run -d --name postgres -e POSTGRES_DB=apollo -e POSTGRES_PASSWORD=iJqHvUqA923TPIkPHKURkXV4 -v database_data:/var/lib/postgresql/data postgres:10-alpine
```

Lastly create a `settings-docker.ini` file containing your application settings in the current directory. A sample of the contents of this file is shown below. Other parameters can be found in the `apollo/settings.py` file.
```
[settings]
SECRET_KEY=GojAgMpHRir9aB6UcJeY3RZ4GJxph9wq
DATABASE_NAME=apollo
DATABASE_PASSWORD=iJqHvUqA923TPIkPHKURkXV4
MAIL_SERVER=smtp.sendgrid.net
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=sendgridusername
MAIL_PASSWORD=sendgridpassword
```

and then start the `worker` and `application` containers.
```
docker run -d --name apollo_worker --link postgres --link redis -v upload_data:/app/uploads -v `pwd`/settings-docker.ini:/app/apollo.ini apollo:latest pipenv run ./manage.py worker
docker run -d --name apollo_app --link postgres --link redis -p 5000:5000 -v upload_data:/app/uploads -v `pwd`/settings-docker.ini:/app/apollo.ini apollo:latest pipenv run ./manage.py gunicorn -c gunicorn.conf
```

Your application is now accessible on port *5000* on the host. You may want to setup a reverse proxy if you are hosting this on the Internet.

Login with the username `admin` and password `admin`. Remember to immediately change the default password.