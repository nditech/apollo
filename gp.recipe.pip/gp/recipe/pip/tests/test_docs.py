# -*- coding: utf-8 -*-
"""
Doctest runner for 'gp.recipe.pip'.
"""
__docformat__ = 'restructuredtext'
import os
import unittest
import zc.buildout.tests
import zc.buildout.testing

from zope.testing import doctest, renormalizing

optionflags =  (doctest.ELLIPSIS |
                doctest.NORMALIZE_WHITESPACE |
                doctest.REPORT_ONLY_FIRST_FAILURE)

def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)

    # Install the recipe in develop mode
    zc.buildout.testing.install_develop('pip', test)
    zc.buildout.testing.install_develop('virtualenv', test)
    zc.buildout.testing.install_develop('distribute', test)
    zc.buildout.testing.install_develop('zc.recipe.egg', test)
    zc.buildout.testing.install_develop('gp.recipe.pip', test)

    # Install any other recipes that should be available in the tests
    #zc.buildout.testing.install('collective.recipe.foobar', test)

def test_suite():
    suite = unittest.TestSuite((
            doctest.DocFileSuite(
                '../README.txt',
                setUp=setUp,
                tearDown=zc.buildout.testing.buildoutTearDown,
                optionflags=optionflags,
                checker=renormalizing.RENormalizing([
                        zc.buildout.testing.normalize_path,
                        ]),
                ),
            doctest.DocFileSuite(
                '../tests.txt',
                setUp=setUp,
                tearDown=zc.buildout.testing.buildoutTearDown,
                optionflags=optionflags,
                checker=renormalizing.RENormalizing([
                        zc.buildout.testing.normalize_path,
                        ]),
                ),
            ))
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
