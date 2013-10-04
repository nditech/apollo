import os
import dotenv
import dj_database_url
from fabric.api import local, put, cd, abort, run, sudo, env, shell_env, settings
from fabric.contrib.files import exists
from fabric.contrib.console import confirm

STAGING_ROOT = "${staging-root}"
PRODUCTION_ROOT = "${production-root}"
SCRIPT_NAME = "${django:control-script}"
APP_SCRIPT = '/etc/init/%s.conf' % (SCRIPT_NAME,)

def app_path(server):
    if server == 'staging':
        return '%s/%s' % (STAGING_ROOT, SCRIPT_NAME)

    elif server == 'production':
        return '%s/%s' % (PRODUCTION_ROOT, SCRIPT_NAME)

    abort("Invalid server path")


def test():
    local('bin/%s test --noinput' % SCRIPT_NAME)


def copyjson(server):
    put('*.json', app_path(server))


def make_archive(version="HEAD"):
    filename = "%s-%s.tar.gz" % (SCRIPT_NAME, version)
    local('git archive --format=tar --prefix=%s/ %s | gzip >%s' % (
        SCRIPT_NAME, version, filename))
    return filename


# Application script actions
def process(action, server="staging", noprompt=False):
    if action in ['start', 'restart', 'stop', 'status']:
        if noprompt or confirm("%s %s on %s?" % (action, SCRIPT_NAME, server)):
            sudo('%s %s' % (action, SCRIPT_NAME), warn_only=True)
    else:
        abort("Invalid action")


def manage(command, server="staging", noprompt=False):
    if noprompt or confirm("Run management command, %s on %s?" % (command, server)):
        with cd(app_path(server)):
            run('bin/%s %s' % (SCRIPT_NAME, command))

def provision(environment="app", server="staging"):
    # provisions an application server or database server
    if local('test -e .env-%s' % (server,), capture=True).succeeded:
        dotenv.read_dotenv('.env-%s' % (server,))
        database_config = dj_database_url.parse(os.environ.get('DATABASE_URL'))
    if confirm("Provision %s server?" % (environment,)):
        if environment == "app":
            sudo('apt-get update')
            sudo('apt-get install -y software-properties-common python-software-properties')
            sudo('add-apt-repository -y ppa:ubuntugis/ppa')
            sudo('apt-get update')
            sudo('apt-get upgrade -y')
            sudo('apt-get install -y vim nginx memcached python-dev build-essential git-core libpq-dev postgresql-client rabbitmq-server librabbitmq-dev libxml2-dev libxslt-dev libproj-dev binutils gdal-bin gettext npm')
            sudo('openssl genrsa -des3 -out /etc/nginx/%s.key 2048' % (SCRIPT_NAME,))
            sudo('openssl rsa -in /etc/nginx/%s.key -out /etc/nginx/%s.key' % (SCRIPT_NAME, SCRIPT_NAME))
            sudo("openssl req -new -key /etc/nginx/%s.key -out /etc/nginx/%s.csr -subj '/CN=%s'" % (SCRIPT_NAME, SCRIPT_NAME, env.host))
            sudo('openssl x509 -req -days 365 -in /etc/nginx/%s.csr -signkey /etc/nginx/%s.key -out /etc/nginx/%s.crt' % (SCRIPT_NAME, SCRIPT_NAME, SCRIPT_NAME))
            sudo('rabbitmqctl add_vhost %s' % (SCRIPT_NAME,))
            sudo('rabbitmqctl set_permissions -p %s guest ".*" ".*" ".*"' % (SCRIPT_NAME,))
            sudo('npm -g install yuglify')
        elif environment == "db":
            sudo('apt-get update')
            sudo('apt-get install -y software-properties-common python-software-properties')
            sudo('add-apt-repository -y ppa:ubuntugis/ppa')
            sudo('apt-get update')
            sudo('apt-get upgrade -y')
            sudo('apt-get install -y vim postgresql postgresql-contrib postgis')

            if database_config:
                sudo('createdb %s' % (database_config['NAME'],), user='postgres')
                sudo('psql -c "CREATE EXTENSION postgis;" %s' % (database_config['NAME'],), user='postgres')
                sudo('psql -c "CREATE EXTENSION hstore;" %s' %(database_config['NAME'],), user='postgres')
        else:
            abort('Choices available for environment are ["app", "db"]')
    else:
        abort("Aborting at user request")

def deploy(server="staging", version="HEAD"):
    if confirm("Deploy %s to %s server?" % (version, server)):
        
        if server == "production":
            root_dir = PRODUCTION_ROOT
            env_name = "PRODUCTION"
        elif server == "staging":
            root = STAGING_ROOT
            env_name = "STAGING"

        if server in ["production", "staging"]:
            archive = make_archive(version)
            run('mkdir -p %s' % root_dir)  # create the directory if it doesn't exist
            put(archive, root_dir)

            with cd(root_dir):
                run('tar zxvf %s' % archive)

            with cd('%s/%s' % (root_dir, SCRIPT_NAME)):
                if local('test -e .env-%s' % (server,), capture=True).succeeded:
                    put('.env-%s' % (server,), '.env')
                else:
                    run('touch .env')
                run('python2.7 init')
                run('set -a && source .env 2>/dev/null && bin/buildout -c production.cfg')
                sudo('ln -sf `pwd`/parts/nginx/%s.conf /etc/nginx/conf.d/' % (SCRIPT_NAME,))
                sudo('bin/honcho export --user %s --app %s --log `pwd`/var/log upstart /etc/init' % (env.user, SCRIPT_NAME,))
                run('mkdir -p assets')
            with cd('%s/%s/eggs/Django-1.4.3-py2.7.egg/django/contrib/gis/db/backends/postgis/' % (root_dir, SCRIPT_NAME)):
                with settings(warn_only=True):
                    run('patch -fsr - <../../../../../../../../templates/creation.patch')
            with cd('%s/%s/eggs/Django-1.4.3-py2.7.egg/django/contrib/gis/geos/' % (root_dir, SCRIPT_NAME)):
                with settings(warn_only=True):
                    run('patch -fsr - <../../../../../../templates/libgeos.patch')
            with cd('%s/%s/lib/python2.7/site-packages/rapidsms/router/db/' % (root_dir, SCRIPT_NAME)):
                with settings(warn_only=True):
                    run('patch -fsr - <../../../../../../templates/router.patch')
            with cd('%s/%s/src/%s' % (root_dir, SCRIPT_NAME, SCRIPT_NAME)):
                run('../../bin/%s compilemessages' % (SCRIPT_NAME,), server, True)

            manage('collectstatic --noinput -l', server, True)
            manage('syncdb --noinput', server, True)
            manage('migrate', server, True)
            process('restart', server, True)
            sudo('service nginx reload')
        else:
            abort('Choices available for server are ["production", "staging"]')
    else:
        abort("Aborting at user request")
