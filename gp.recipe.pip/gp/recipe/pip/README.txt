Supported options
=================

The recipe supports the following options:

.. Note to recipe author!
   ----------------------
   For each option the recipe uses you shoud include a description
   about the purpose of the option, the format and semantics of the
   values it accepts, whether it is mandatory or optional and what the
   default value is if it is omitted.

virtualenv

    Virtualenv directory. The virtualenv is build in this directory (Default to
    `parts/pip`). You can also use an existing one. If a `virtualenv` option is
    found in the buildout section then this one is used except if the current
    section override it.

env
    extra environement vars used with subprocess

indexes
    Extra indexes url.

install
    A list of string passed to pip directly. A sub process is run per line.
    This allow to use `--install-option`.

editables
    A list of svn url. (`svn+http://myrepo/svn/MyApp#egg=MyApp`)

eggs
    A list of distribution to install with buildout

This recipe is based on `zc.recipe.egg#scripts
<http://pypi.python.org/pypi/zc.recipe.egg#id23>`_ so options used by this
recipe should also works.

Example usage
=============

We'll start by creating a buildout that uses the recipe::

    >>> write('buildout.cfg',
    ... """
    ... [buildout]
    ... parts = test1
    ...
    ... [test1]
    ... recipe = gp.recipe.pip
    ... install =
    ...     PasteScript
    ... interpreter = python
    ... scripts =
    ...     paster = paster
    ... """)

Running the buildout gives us::

    >>> print 'start', system(buildout) 
    start...
    Installing test1.
    ...
    Generated script '/sample-buildout/bin/paster'.
    Generated interpreter '/sample-buildout/bin/python'...

Scripts are generated::

    >>> ls('bin')
    -  buildout
    -  paster
    -  python

With the virtualenv binary as executable::

    >>> print 'cat', cat('bin', 'paster')
    cat .../parts/pip/bin/python
    ...

Complete Example
================

Here is a config file used to install Deliverance::

  [buildout]
  parts = eggs
  download-cache = download
  versions = versions

  [versions]
  # the recipe take care of versions
  lxml=2.2alpha1

  [eggs]
  recipe = gp.recipe.pip
  # needed to build static libs for lxml 
  env =
      STATIC_DEPS=true

  # packages to install with pip
  install =
      Cython
      --install-option=--static-deps lxml
      http://deliverance.openplans.org/dist/Deliverance-snapshot-latest.pybundle

  # packages to install with buildout
  eggs =
      pyquery

  # svn urls
  editables =
      svn+http://...

