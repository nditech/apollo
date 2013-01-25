from fabric.api import local, put, cd, abort, run
from fabric.contrib.files import exists
from fabric.contrib.console import confirm


STAGING_ROOT = "${staging-root}"
PRODUCTION_ROOT = "${production-root}"
SCRIPT_NAME = "${django:control-script}"
APP_SCRIPT = './%s/bin/%s.sh' % (SCRIPT_NAME, SCRIPT_NAME)


def app_path(server):
    if server == 'staging':
        return '%s/%s' % (STAGING_ROOT, SCRIPT_NAME)

    elif server == 'production':
        return '%s/%s' % (PRODUCTION_ROOT, SCRIPT_NAME)

    abort("Invalid server path")


def test():
    local('./bin/%s test' % SCRIPT_NAME)


def copyjson(server):
    put('*.json', app_path(server))


def make_archive(version="HEAD"):
    filename = "%s-%s.tar.gz" % (SCRIPT_NAME, version)
    local('git archive --format=tar --prefix=%s/ %s | gzip >%s' % (
        SCRIPT_NAME, version, filename))
    return filename


# Application script actions
def process(action, server="staging"):
    if action in ['start', 'restart', 'stop', 'check']:
        if confirm("%s %s on %s?" % (action, SCRIPT_NAME, server)):
            with cd(app_path(server)):
                run('sh ./bin/%s.sh %s' % (SCRIPT_NAME, action))
    else:
        abort("Invalid action")


def manage(command, server="staging"):
    if confirm("Run management command, %s on %s?" % (command, server)):
        with cd(app_path(server)):
            run('./bin/%s %s' % (SCRIPT_NAME, command))


def deploy(server="staging", version="HEAD"):
    if confirm("Deploy %s to %s server?" % (version, server)):

        if server == "staging":
            # local('./bin/%s test' % SCRIPT_NAME)

            archive = make_archive(version)
            put(archive, PRODUCTION_ROOT)

            with cd(STAGING_ROOT):
                # Stop the process if it's running before continuing
                if exists(APP_SCRIPT):
                    run('sh %s stop' % APP_SCRIPT)
                run('tar zxvf %s' % archive)

            with cd('%s/%s' % (STAGING_ROOT, SCRIPT_NAME)):
                run('python2.7 bootstrap.py -c staging.cfg')
                run('./bin/buildout -c staging.cfg')

        elif server == "production":
            # local('./bin/%s test' % SCRIPT_NAME)

            archive = make_archive(version)
            put(archive, PRODUCTION_ROOT)

            with cd(PRODUCTION_ROOT):
                # Stop the process if it's running before continuing
                if exists(APP_SCRIPT):
                    run('sh %s stop' % APP_SCRIPT)

                run('tar zxvf %s' % archive)

            with cd('%s/%s' % (PRODUCTION_ROOT, SCRIPT_NAME)):
                run('python2.7 bootstrap.py -c production.cfg')
                run('./bin/buildout -c production.cfg')

    else:
        abort("Aborting at user request")
