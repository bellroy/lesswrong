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
import os
import sys
from unittest import TestCase

here_dir = os.path.dirname(os.path.abspath(__file__))
conf_dir = os.path.dirname(os.path.dirname(here_dir))

sys.path.insert(0, conf_dir)

import pkg_resources

pkg_resources.working_set.add_entry(conf_dir)

pkg_resources.require('Paste')
pkg_resources.require('PasteScript')

from paste.deploy import loadapp
import paste.fixture
import paste.script.appinstall

from r2.config.routing import *
from routes import request_config, url_for
from paste.registry import Registry
from r2.lib.app_globals import Globals
from paste.deploy import appconfig

from r2.templates import tmpl_dirs
import os
import pylons
from pylons.i18n.translation import NullTranslations
from pylons.util import ContextObj

test_file = os.path.join(conf_dir, 'test.ini')
cmd = paste.script.appinstall.SetupCommand('setup-app')
cmd.run([test_file])

class TestController(TestCase):
    def __init__(self, *args):
        wsgiapp = loadapp('config:test.ini', relative_to=conf_dir)
        self.app = paste.fixture.TestApp(wsgiapp)
        self.app.extra_environ['REMOTE_ADDR'] = '127.0.0.1'
        TestCase.__init__(self, *args)

class ModelTest(object):
    def __init__(self):
        config = appconfig('config:test.ini', relative_to=conf_dir)
        root_path = os.path.join(conf_dir, 'r2')
        paths = {
            'root': root_path,
             'controllers': os.path.join(root_path, 'controllers'),
             'templates': tmpl_dirs,
             'static_files': os.path.join(root_path, 'public')
         }

        self.registry = Registry()
        self.registry.prepare()
        self.globals = Globals(config.global_conf, config.local_conf, paths)
        self.registry.register(pylons.g, self.globals)
        self.registry.register(pylons.translator, NullTranslations())
        self.context_obj=ContextObj()
        self.registry.register(pylons.c, self.context_obj)

        self.models = __import__('r2.models', fromlist=['r2']) # XXX Horrible hack


__all__ = ['url_for', 'TestController']
