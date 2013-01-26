# -*- coding: utf-8 -*-
"""
This module contains the tool of gp.recipe.pip
"""
import os
from setuptools import setup, find_packages

def read(*rnames):
    return open(os.path.join('.', *rnames)).read()

version = '0.5.3'

long_description = (
    read('README.txt')
    + '\n' +
    'Detailed Documentation\n'
    '**********************\n'
    + '\n' +
    read('gp', 'recipe', 'pip', 'README.txt')
    + '\n' +
    'Contributors\n'
    '************\n'
    + '\n' +
    read('CONTRIBUTORS.txt')
    + '\n' +
    'Change history\n'
    '**************\n'
    + '\n' +
    read('CHANGES.txt')
    + '\n' +
   'Download\n'
    '********\n'
    )
entry_point = 'gp.recipe.pip:Recipe'
entry_points = {"zc.buildout": ["default = %s" % entry_point]}

tests_require=['zope.testing', 'zc.buildout']

setup(name='gp.recipe.pip',
      version=version,
      description="zc.buildout recipe for pip",
      long_description=long_description,
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        'Framework :: Buildout',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        ],
      keywords='buildout pip',
      author='Gael Pasgrimaud',
      author_email='gael@gawel.org',
      url='http://www.bitbucket.org/gawel/gprecipepip/',
      license='MIT',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['gp', 'gp.recipe'],
      include_package_data=True,
      zip_safe=False,
      install_requires=['distribute',
                        'zc.buildout',
                        'zc.recipe.egg',
                        'virtualenv>=1.4',
                        'pip',
                        ],
      tests_require=tests_require,
      extras_require=dict(tests=tests_require),
      test_suite = 'gp.recipe.pip.tests.test_docs.test_suite',
      entry_points=entry_points,
      )
