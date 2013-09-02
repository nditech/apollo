# -*- coding: utf-8 -*-
"""Recipe pip"""
import pkg_resources
import zc.buildout
import zc.buildout.easy_install
from zc.recipe.egg import Scripts
from subprocess import call
from copy import deepcopy
from os.path import join
import virtualenv
import logging
import glob
import sys
import os

PYTHON = 'python%s' % sys.version[0:3]

PYPI_URL='http://pypi.python.org/simple'

def to_list(value):
    value = value.split('\n')
    value = [v.strip() for v in value]
    value = [v for v in value if v]
    return value

def get_executable(part_dir):
    for bin in ('python', PYTHON, 'Python.exe', '%s.exe' % PYTHON.title()):
        executable = join(part_dir, 'bin', bin)
        if os.path.isfile(executable):
            break
    return executable

class Recipe(Scripts):
    """zc.buildout recipe"""

    def pip_install(self, part_dir, build_dir, src_dir, extra_args):
        print 'pip install %s' % ' '.join(extra_args)

        # pop command line arguments
        args = ['install',
                '-i', self.buildout['buildout'].get('index', PYPI_URL),
                '--log', '%s-log.txt' % self.name,
                '-b', build_dir,
                '--src', src_dir,
               ]

        if 'find-links' in self.buildout['buildout']:
            for l in to_list(self.buildout['buildout']['find-links']):
                if os.path.isdir(l):
                    args.extend(['-f', "file:///" + l])
                else:
                    args.extend(['-f', l])

        indexes = to_list(self.options.get('indexes', ''))
        for o in indexes:
            args.append('--extra-index-url=%s' % o)

        install_options = to_list(self.options.get('install-options', ''))
        for o in install_options:
            args.append('--install-option=%s' % o)


        include_dir = join(part_dir, 'include', PYTHON)
        executable = get_executable(part_dir)

        # try to use venv executable if already avalaible
        if os.path.isfile(executable):
            cmd = [executable, '-c']
        else:
            cmd = [sys.executable, '-c']

        # command line
        cmd.append('"from pip import main; main(%r)"' % (args+extra_args,))

        # subprocess environ
        env = os.environ.copy()
        env.update(dict([v.split('=') for v in to_list(self.options.get('env',''))]))
        orig_cflags = env.get('CFLAGS', '')
        if orig_cflags:
            orig_cflags += ' '
        env.update({
             'PYTHONPATH': ':'.join(sys.path),
             'CFLAGS': '%s-I%s' % (orig_cflags, include_dir),
             'LDFLAGS': '-I%s' % include_dir,
             })

        # pip cache
        if 'download-cache' in self.buildout['buildout']:
             env['PIP_DOWNLOAD_CACHE'] = self.buildout['buildout'].get('download-cache')

        # call pip
        #print sorted(env.keys())
        #print 'PYTHONPATH=%s' % env['PYTHONPATH']
        #print ' '.join(cmd)
        code = call(' '.join(cmd), shell=True, env=env)
        if code != 0:
            raise RuntimeError('An error occur during pip installation. See %s-log.txt' % self.name)

    def working_set(self, extra=()):
        options = self.options

        part_dir = join(self.buildout['buildout']['parts-directory'], 'pip')
        if 'virtualenv' in self.buildout['buildout']:
            part_dir = self.buildout['buildout']['virtualenv']
        if 'virtualenv' in options:
            part_dir = options['virtualenv']

        build_dir = join(part_dir, 'build')
        if 'build-directory' in self.buildout['buildout']:
            build_dir = self.buildout['buildout']['build-directory']
        if 'build-directory' in options:
            build_dir = options['build-directory']

        src_dir = options.get('sources-directory',
                              join(self.buildout['buildout']['directory'], 'src'))

        # get buildout versions
        versions_option = self.buildout['buildout'].get('versions')
        if versions_option:
            buildout_versions = dict(self.buildout[versions_option])
        else:
            buildout_versions = {}

        # pip installs

        # venv
        #self.pip_install(part_dir, build_dir, src_dir, [])
        if not os.path.isdir(part_dir):
            virtualenv.logger = virtualenv.Logger([(virtualenv.Logger.level_for_integer(2), sys.stdout)])
            virtualenv.create_environment(part_dir, site_packages=False,
                                          use_distribute=True)

        # VSC
        editables = to_list(options.get('editables', ''))
        for e in editables:
            self.pip_install(part_dir, build_dir, src_dir, ['-e', e])

        # packages / bundles. add version if needed
        installs = to_list(options.get('install', ''))
        for i in installs:
            for k in buildout_versions:
                if i.endswith(k):
                    i = '%s==%s' % (i, buildout_versions.get(k))
            self.pip_install(part_dir, build_dir, src_dir, i.split())


        # prepare options for zc.recipe.egg

        # retrieve venv's site-packages and executable
        executable = get_executable(part_dir)
        assert os.path.isfile(executable)
        options['executable'] = executable

        site_packages = glob.glob(join(part_dir, 'lib', '*', 'site-packages'))[0]
        assert os.path.isdir(site_packages)

        # move .egg-link from site-packages and append develop eggs to eggs list
        dev_eggs_dir = self.buildout['buildout']['develop-eggs-directory']
        for filename in glob.glob(join(site_packages, '*.egg-link')):
            name =  os.path.basename(filename)
            os.rename(filename, join(dev_eggs_dir, name))

        # This came from zc.recipe.egg but we need to add venv's WorkingSet
        ws = workink_set=pkg_resources.WorkingSet([site_packages])

        kw = {}
        always_unzip = options.get('unzip')
        if always_unzip is not None:
            if always_unzip not in ('true', 'false'):
                raise zc.buildout.UserError("Invalid value for unzip, %s"
                                            % always_unzip)
            kw['always_unzip'] = always_unzip == 'true'

        distributions = to_list(options.get('eggs', ''))
        ws = zc.buildout.easy_install.install(
            distributions,
            options['eggs-directory'],
            links = self.links,
            index = self.index,
            executable = executable,
            path=[options['develop-eggs-directory']],
            newest=self.buildout['buildout'].get('newest') == 'true',
            allow_hosts=self.allow_hosts,
            working_set=ws,
            **kw)

        distributions.extend([d.project_name for d in ws])

        return distributions, ws


    def install(self):
        if self.buildout['buildout']['offline'] == 'true':
            return ()
        return Scripts.install(self)
