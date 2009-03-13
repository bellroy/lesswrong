import r2.tests
import nose
from paste.registry import Registry
from r2.lib.app_globals import Globals
from paste.deploy import appconfig

# from r2.config.environment import load_environment
from r2.templates import tmpl_dirs
import os
import pylons
from pylons.i18n.translation import NullTranslations


class TestLink(object):
    
    def setup(self):
        # response = self.app.get('/') # Hack that sets up the global environment
        config = appconfig('config:test.ini', relative_to=r2.tests.conf_dir)
        root_path = os.path.join(r2.tests.conf_dir, 'r2')
        paths = {'root': root_path,
                 'controllers': os.path.join(root_path, 'controllers'),
                 'templates': tmpl_dirs,
                 'static_files': os.path.join(root_path, 'public')
                 }

        self.registry = Registry()
        self.registry.prepare()
        self.globals = Globals(config.global_conf, config.local_conf, paths)
        self.registry.register(pylons.g, self.globals)

        self.registry.register(pylons.translator, NullTranslations())

        # Create a link here
        self.link = { 'name': 'Link Name' }
        from r2.models import Link  
    
    def teardown(self):
        # drop Link here
        self.link = None
    
    def test_name(self):
        print self.link
        assert self.link['name'] == 'Link Name'

