# Description: Unit tests for packstats module

import unittest
import time
import logging
import logging.handlers
from packstats import stats, utils

config = utils.Config.instance()


class TestPackstats(unittest.TestCase):
    def setUp(self):
        self.log = logging.getLogger("unittest")
        self.log.setLevel(logging.DEBUG)
        self.logfile = config["DEFAULT_LOG_DIR_PATH"] + "unittest.log"
        self.loghandler = logging.handlers.RotatingFileHandler(
            self.logfile, maxBytes=100000, backupCount=5
        )
        self.loghandler.setLevel(logging.DEBUG)
        self.loghandler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(message)s")
        )
        self.log.addHandler(self.loghandler)
        self.log.info("Test started")

        # Setup PackageStatistics object
        self.arch = "amd64"
        self.mirror_url = "http://ftp.uk.debian.org/debian/dists/stable/main/"
        self.top_n = 10
        self.refresh = False

    def test_init_packstats(self):
        self.log.info("Testing PackageStatistics object initialization")
        packstats = stats.PackageStatistics(
            self.arch, self.mirror_url, self.top_n, self.refresh
        )
        self.assertEqual(packstats.arch, self.arch)
        self.assertEqual(packstats.mirror_url, self.mirror_url)
        self.assertEqual(packstats.top_packs_count, self.top_n)
        self.assertEqual(packstats.refresh, self.refresh)

    def test_get_top_packages(self):
        self.log.info("Testing get_top_packages method")
        packstats = stats.PackageStatistics(
            self.arch, self.mirror_url, self.top_n, self.refresh
        )
        self.assertEqual(len(packstats.get_top_packages()), self.top_n)

    def test_get_top_packages_with_refresh(self):
        self.log.info("Testing get_top_packages method with refresh")
        packstats = stats.PackageStatistics(
            self.arch, self.mirror_url, self.top_n, True
        )
        self.assertEqual(len(packstats.get_top_packages()), self.top_n)

    def test_get_top_packages_with_refresh_and_invalid_mirror_url(self):
        self.log.info(
            "Testing get_top_packages method with refresh and invalid mirror url"
        )
        with self.assertRaises(SystemExit):
            stats.PackageStatistics(
                self.arch, "http://invalid_mirror_url", self.top_n, False
            )

    def test_get_top_packages_with_refresh_and_invalid_arch(self):
        self.log.info("Testing get_top_packages method with refresh and invalid arch")
        with self.assertRaises(SystemExit):
            stats.PackageStatistics("invalid_arch", self.mirror_url, self.top_n, False)

    def test_get_top_packages_with_refresh_and_invalid_top_n(self):
        self.log.info("Testing get_top_packages method with refresh and invalid top_n")
        with self.assertRaises(SystemExit):
            stats.PackageStatistics(self.arch, self.mirror_url, -1, False)
        with self.assertRaises(SystemExit):
            stats.PackageStatistics(self.arch, self.mirror_url, 0, False)

    def test_time_improvment_after_refresh(self):
        self.log.info("Testing time improvment after refresh")
        fresh_stat = time.time()
        packstats = stats.PackageStatistics(
            self.arch, self.mirror_url, self.top_n, True
        )
        packstats.print_top_packages()
        fresh_end = time.time()
        cached_start = time.time()
        packstats = stats.PackageStatistics(
            self.arch, self.mirror_url, self.top_n, False
        )
        packstats.print_top_packages
        cached_end = time.time()
        self.assertLess(cached_end - cached_start, fresh_end - fresh_stat)

    def tearDown(self):
        self.log.info("Test finished")
        self.log.removeHandler(self.loghandler)
