from fabric.api import sudo, run, local, put, cd

PROJECT_NAME = 'apollo'
PROJECT_DIR = 'projects'

def get_current_branch():
    current_branch = local("git branch --no-color | grep '^\* ' | grep -v 'no branch' | sed 's/^* //g'", capture=True)
    return current_branch

def change_branch(branch='master'):
    return local('git checkout %s' % branch)

def get_latest_version():
    return local("git tag -l | tail -n 1 | sed -e 's/^v//g'", capture=True)

def make_archive(version="HEAD"):
    filename = "%s-%s.tar.gz" % (PROJECT_NAME, version)
    local('git archive --format=tar --prefix=%s/ %s | gzip >%s' % (
        PROJECT_NAME, version, filename))
    return filename


def tag(docker_index, image_version):
    sudo('docker tag -f %s %s/%s:%s' % (
        PROJECT_NAME, docker_index, PROJECT_NAME, image_version))
    sudo('docker tag -f %s %s/%s:latest' % (
        PROJECT_NAME, docker_index, PROJECT_NAME))


def push(docker_index, image_version):
    sudo('docker push %s/%s:%s' % (
        docker_index, PROJECT_NAME, image_version))
    sudo('docker push %s/%s:latest' % (
        docker_index, PROJECT_NAME))


def build(docker_index='docker.timbaobjects.com', version="HEAD"):
    current_branch = get_current_branch()
    image_version = get_latest_version()
    change_branch('master')
    archive = make_archive(version)
    run('rm -rf %s' % PROJECT_DIR)  # remove the target directory if it exists
    run('mkdir -p %s' % PROJECT_DIR)  # create target directory
    put(archive, PROJECT_DIR)
    with cd(PROJECT_DIR):
        run('tar xzf %s' % archive)

    with cd('%s/%s' % (PROJECT_DIR, PROJECT_NAME)):
        sudo('docker build --rm=false -t %s .' % PROJECT_NAME)
    tag(docker_index, image_version)
    push(docker_index, image_version)
    change_branch(current_branch)

