#!/usr/bin/env python

# The contents of this file are subject to the Common Public Attribution
# License Version 1.0. (the "License"); you may not use this file except in
# compliance with the License. You may obtain a copy of the License at
# http://code.reddit.com/LICENSE. The License is based on the Mozilla Public
# License Version 1.1, but Sections 14 and 15 have been added to cover use of
# software over a computer network and provide for limited attribution for the
# Original Developer. In addition, Exhibit A has been modified to be consistent
# with Exhibit B.
# 
# Software distributed under the License is distributed on an "AS IS" basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License for
# the specific language governing rights and limitations under the License.
# 
# The Original Code is Reddit.
# 
# The Original Developer is the Initial Developer.  The Initial Developer of the
# Original Code is CondeNet, Inc.
# 
# All portions of the code written by CondeNet are Copyright (c) 2006-2008
# CondeNet, Inc. All Rights Reserved.
################################################################################

from ez_setup import use_setuptools
use_setuptools()
from setuptools import find_packages#, setup

try:
    from babel.messages import frontend as babel
except:
    class null(): pass
    babel = null()
    babel.compile_catalog = None
    babel.extract_messages = None
    babel.init_catalog = None
    babel.update_catalog = None

from distutils.core import setup, Extension

from setuptools.command.easy_install import main as easy_install

# check the PIL is installed; since its package name isn't the same as
# the distribution name, setuptools can't manage it as a dependency
try:
    import Image
except ImportError:
    print "Installing the Python Imaging Library"
    easy_install(["http://effbot.org/downloads/Imaging-1.1.6.tar.gz"])

# same with the captcha library
try:
    import Captcha
except ImportError:
    print "Installing the PyCaptcha Module"
    easy_install(["http://svn.navi.cx/misc/trunk/pycaptcha"])
    
# unfortunately, we use an old version of sqlalchemy right now
try:
    import sqlalchemy
    vers = sqlalchemy.__version__ 
    assert vers == "0.3.10", \
           ("reddit is only compatible with SqlAlchemy 0.3.10 not '%s' " % vers)
except ImportError:
    print "Installing Sqlalchemy 0.3.10 from the cheese shop"
    easy_install(["http://pypi.python.org/packages/source/S/SQLAlchemy/SQLAlchemy-0.3.10.tar.gz"])

filtermod = Extension('Cfilters',
                      sources = ['r2/lib/c/filters.c'])

# GeoIP isn't in the Python package index so need to install semi-manually
try:
    import GeoIP
except ImportError:
    print "You need to install the GeoIP python package."
    print "On Debian Linux and derivations: install the python-geoip package"
    print "otherwise install manually from: http://www.maxmind.com/app/python"
    raise Exception

setup(
    name='r2',
    version="",
    #description="",
    #author="",
    #author_email="",
    #url="",
    dependency_links=[
        'http://www.crummy.com/software/BeautifulSoup/download/3.x/',
    ],
    install_requires=["WebHelpers==0.6.4",
                      "Routes<=1.8",
                      "Beaker==1.5.1",
                      "Paste==1.7.2",
                      "PasteDeploy==1.3.3",
                      "PasteScript==1.7.2",
                      "Pylons==0.9.6.2",
                      "pycrypto==2.0.1",
                      "Babel==0.9.5",
                      "flup<=1.0.3",
                      "simplejson==2.1.1",
                      "SQLAlchemy==0.3.10",
                      "BeautifulSoup==3.0.7a",
                      "cssutils==0.9.5.1",
                      "chardet==1.0.1",
                      "psycopg2==2.2.1",
                      "py_interface==0.93",
                      "lxml==2.2.6",
                      "PyYAML==3.09",
                      "pytz", # Best to keep up with DST updates (so no specific version)
                      "geolocator==0.1.1",
                      ],
    packages=find_packages(),
    include_package_data=True,
    test_suite = 'nose.collector',
    package_data={'r2': ['i18n/*/LC_MESSAGES/*.mo']},
    cmdclass = {'compile_catalog':      babel.compile_catalog,
                'extract_messages':     babel.extract_messages,
                'init_catalog':         babel.init_catalog,
                'update_catalog':       babel.update_catalog,
                },
    ext_modules = [filtermod],
    entry_points="""
    [paste.app_factory]
    main=r2:make_app
    [paste.app_install]
    main=pylons.util:PylonsInstaller
    [paste.paster_command]
    run = r2.commands:RunCommand
    shell = pylons.commands:ShellCommand
    controller = pylons.commands:ControllerCommand
    restcontroller = pylons.commands:RestControllerCommand
    """,
)


