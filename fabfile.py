from fabric.api import sudo, run, local, put, cd

PROJECT_NAME = 'apollo'
PROJECT_DIR = 'projects'


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


def build(
    image_version, docker_index='docker.timbaobjects.com', version="HEAD"
):
    archive = make_archive(version)
    run('mkdir -p %s' % PROJECT_DIR)  # create target directory
    put(archive, PROJECT_DIR)
    with cd(PROJECT_DIR):
        run('tar xzf %s' % archive)

    with cd('%s/%s' % (PROJECT_DIR, PROJECT_NAME)):
        sudo('docker build -t %s .' % PROJECT_NAME)
    tag(docker_index, image_version)
    push(docker_index, image_version)
