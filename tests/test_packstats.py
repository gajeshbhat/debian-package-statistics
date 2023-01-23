# Desc: test packstats module

import unittest
import os
import shutil
import tempfile
import logging
import logging.handlers


from packstats import *

class TestPackstats(unittest.TestCase):
    
        def setUp(self):
            self.tmpdir = tempfile.mkdtemp()
            self.log = logging.getLogger('packstats')
            self.log.setLevel(logging.DEBUG)
            self.logfile = os.path.join(self.tmpdir, 'tests.log')
            self.loghandler = logging.handlers.RotatingFileHandler(self.logfile, maxBytes=100000, backupCount=5)
            self.loghandler.setLevel(logging.DEBUG)
            self.loghandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
            self.log.addHandler(self.loghandler)
            self.log.info('Test started')
    
        def tearDown(self):
            self.log.info('Test finished')
            self.log.removeHandler(self.loghandler)
            shutil.rmtree(self.tmpdir)