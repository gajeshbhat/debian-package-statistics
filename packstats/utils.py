import os
import sys
from typing import List
from urllib.parse import urlparse
from urllib.request import urlopen
import time
import json
import logging.handlers

# Class to handle logging for .stats and .utils modules
class Logger:
    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path
        self.setup_log_folder()
        self.log = logging.getLogger('packstats')
        self.log.setLevel(logging.DEBUG)
        self.loghandler = logging.handlers.RotatingFileHandler(self.log_file_path, maxBytes=100000, backupCount=5)
        self.loghandler.setLevel(logging.DEBUG)
        self.loghandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        self.log.addHandler(self.loghandler)
        self.log.info("\n") # Two space between each run
    
    def setup_log_folder(self):
        config = Config.instance()
        if not os.path.exists(config["DEFAULT_LOG_DIR_PATH"]):
            os.makedirs(config["DEFAULT_LOG_DIR_PATH"])
        
    def get_logger(self):
        return self.log

    def get_log_file_path(self):
        return self.log_file_path

    def remove_log_handler(self):
        self.log.removeHandler(self.loghandler)
    
    def log_info(self, message: str):
        self.log.info(message)

    def log_debug(self, message: str):
        self.log.debug(message)

    def log_warning(self, message: str):
        self.log.warning(message)

    def log_error(self, message: str):
        self.log.error(message)


# Singleton class to load the configuration file    
class Config(object):
    _instance = None

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = cls._get_config()
        return cls._instance
    
    @classmethod
    def _get_config(cls):
        # Read the configuration file from the config directory
        try:
            with open("./config/packstat_defaults.json", "r") as f:
                config = json.load(f)
            return config
        except Exception as e:
            print("An error occurred while trying to load the configuration file! ", e)
            print("Using default configuration values instead and saving them in a ./config/packstat_defaults.json file.")

            # Save the default configuration values in a file
            os.makedirs("./config", exist_ok=True)
            with open("./config/packstat_defaults.json", "w") as f:
                json.dump(cls._get_default_config(), f, indent=4)
            return cls._get_default_config()
        
    @classmethod
    def _get_default_config(cls):
        return {
                "DEFAULT_MIRROR_URL": "http://ftp.uk.debian.org/debian/dists/stable/main/",
                "DEFAULT_TOP_N": 10,
                "DEFAULT_REFRESH": False,
                "DEFAULT_ARCH": "all",
                "DEFAULT_DATA_DIR_PATH": "./data/"
                }

# Load the configuration file
config = Config.instance()

# Check if the available architectures file and if its older than the given number of days
class ArchUtils:
    DEFAULT_DATA_DIR_PATH = config["DEFAULT_DATA_DIR_PATH"]
    DEFAULT_MIRROR_URL = config["DEFAULT_MIRROR_URL"]
    LOG_FILE_PATH = config["DEFAULT_LOG_DIR_PATH"] + "packstats.log"

    def __init__(self, mirror_url: str):
        self.logger = Logger(ArchUtils.LOG_FILE_PATH)
        self.mirror_url = mirror_url
        self.mirror_domain = self.get_mirror_domain()
        self.arch_file_path = ArchUtils.DEFAULT_DATA_DIR_PATH + f"{self.mirror_domain}/" + "/available_archs.txt"
    
    def get_mirror_domain(self) -> str:
        return urlparse(self.mirror_url).netloc
    
    def validate_and_create_archs(self, arch: str) -> bool:
        """
        Check if the given architecture is available on the mirror
        """
        self.logger.log_info(f"Validating architecture {arch} on mirror {self.mirror_domain}")
        # If the available architectures file exists and is not older than 1 day, use it
        if os.path.exists(self.arch_file_path) and not self.is_available_arch_older_than(1):
            with open(self.arch_file_path, "r") as f:
                archs = f.read().splitlines()
                if arch not in archs:
                    print("The given architecture is not available on this Debian Mirror")
                    self.logger.log_error(f"The given architecture {arch} is not available on this Debian Mirror {self.mirror_domain}")
                    sys.exit(1)
                else:
                    return True
        else:
            # If the available architectures file doesn't exist, create it
            self.logger.log_info(f"Creating available architectures file for mirror {self.mirror_domain}")
            os.makedirs(ArchUtils.DEFAULT_DATA_DIR_PATH + f"{self.mirror_domain}", exist_ok=True)
            self.create_arch_file()
            return True if self.validate_and_create_archs(arch) else False
            
    def create_arch_file(self, mirror_url: str = DEFAULT_MIRROR_URL) -> List[str]:
        try:
            self.logger.log_info(f"Creating available architectures file for mirror {self.mirror_domain}")
            with urlopen(mirror_url) as response:
                raw_html = response.read()
                html = raw_html.decode("utf-8")

            # Find the available architectures
            archs = html.split("Contents-")[1:]
            valid_archs = [arch.split(".gz")[0] for arch in archs]
            self.logger.log_info(f"Available architectures for mirror {self.mirror_domain}: {valid_archs}")

            # Save the available architectures in a file
            with open(self.arch_file_path, "w") as f:
                # Remove duplicates
                for arch in list(set(valid_archs)):  
                    f.write(arch + "\n")
            return valid_archs
        except Exception as e:
            self.logger.log_error(f"An error occurred while trying to retrieve the available architectures for mirror {self.mirror_domain}: {e}")
            print("An error occurred while trying to retrieve the available architectures!")
            sys.exit(1)
    
    def is_available_arch_older_than(self, days: int) -> bool:
        # Check if the available architectures file is older than the given number of days
        self.logger.log_info(f"Checking if available architectures file for mirror {self.mirror_domain} is older than {days} days")
        arch_file_path = self.arch_file_path
        if os.path.exists(arch_file_path):
            arch_file_mod_time = os.path.getmtime(arch_file_path)
            if arch_file_mod_time < (time.time() - (days * 24 * 60 * 60)):
                self.logger.log_info(f"Available architectures file for mirror {self.mirror_domain} is older than {days} days and needs an update")
                return True
            else:
                self.logger.log_info(f"Available architectures file for mirror {self.mirror_domain} is not older than {days} days. Continuing...")
                return False
        else:
            return True
        

