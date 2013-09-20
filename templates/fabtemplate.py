import os
import dotenv
from fabric.api import local, put, cd, abort, run, sudo, env, shell_env
from fabric.contrib.files import exists
from fabric.contrib.console import confirm

dotenv.read_dotenv(os.path.realpath('.env'))

env.hosts = [os.environ.get('FABRIC_HOSTS')]
env.user = os.environ.get('FABRIC_USER')

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

def provision(server="app"):
    # provisions an application server or database server
    if confirm("Provision %s server?" % (server,)):
        if server == "app":
            sudo('apt-get update')
            sudo('apt-get upgrade')
            sudo('apt-get install nginx memcached python-dev build-essential')
        elif server == "db":
            sudo('apt-get update')
            sudo('apt-get upgrade')
            sudo('apt-get install postgresql-server')
        else:
            abort('Choices available for server are ["app", "db"]')
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
                # Stop the process if it's running before continuing
                if exists(APP_SCRIPT):
                    process('stop', server, True)
                run('tar zxvf %s' % archive)

            with cd('%s/%s' % (root_dir, SCRIPT_NAME)):
                if local('test -e .env-%s' % (server,), capture=True).succeeded:
                    put('.env-%s' % (server,), '.env')
                run('./init')
                run('set -a && source .env 2>/dev/null || bin/buildout -c production.cfg')
                sudo('ln -sf ${buildout:parts-directory}/nginx/%s.conf /etc/nginx/sites-available/' % (SCRIPT_NAME,))
                sudo('bin/honcho export -a %s -l ${buildout:directory}/var/log upstart /etc/init' % (SCRIPT_NAME,))
                run('mkdir -p assets')
            with cd('%s/%s/src/%s' % (root_dir, SCRIPT_NAME, SCRIPT_NAME)):
                manage('../../bin/%s compilemessages' % (SCRIPT_NAME,), server, True)

            manage('collectstatic --noinput -l', server, True)
            manage('syncdb --noinput', server, True)
            manage('migrate', server, True)
            process('start', server, True)
            sudo('service nginx reload')
        else:
            abort('Choices available for server are ["production", "staging"]')
    else:
        abort("Aborting at user request")
