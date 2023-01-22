import os
import sys
from typing import List
from urllib.parse import urlparse
from urllib.request import urlopen
import time
import json

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
        with open("./config/packstat_defaults.json", "r") as f:
            config = json.load(f)
        return config


# Load the configuration file
config = Config.instance()

# Check if the available architectures file and if its older than the given number of days
class ArchUtils:
    DEFAULT_DATA_DIR_PATH = config["DEFAULT_DATA_DIR_PATH"]
    DEFAULT_MIRROR_URL = config["DEFAULT_MIRROR_URL"]

    def __init__(self, mirror_url: str):
        self.mirror_url = mirror_url
        self.mirror_domain = self.get_mirror_domain()
        self.arch_file_path = ArchUtils.DEFAULT_DATA_DIR_PATH + f"{self.mirror_domain}/" + "/available_archs.txt"
    
    def get_mirror_domain(self) -> str:
        return urlparse(self.mirror_url).netloc
    
    def validate_arch(self, arch: str) -> bool:
        """
        Check if the given architecture is available on the mirror
        """
        # If the available architectures file exists and is not older than 1 day, use it
        if os.path.exists(self.arch_file_path) and not self.is_available_arch_older_than(1):
            with open(self.arch_file_path, "r") as f:
                archs = f.read().splitlines()
                if arch not in archs:
                    print("The given architecture is not available on this Debian Mirror")
                    sys.exit(1)
                else:
                    return True
        else:
            # If the available architectures file doesn't exist, create it
            os.makedirs(ArchUtils.DEFAULT_DATA_DIR_PATH + f"{self.mirror_domain}", exist_ok=True)
            self.create_arch_file()
            return self.validate_arch(arch)
            
    def create_arch_file(self, mirror_url: str = DEFAULT_MIRROR_URL) -> List[str]:
        try:
            with urlopen(mirror_url) as response:
                raw_html = response.read()
                html = raw_html.decode("utf-8")

            # Find the available architectures
            archs = html.split("Contents-")[1:]
            valid_archs = [arch.split(".gz")[0] for arch in archs]

            # Save the available architectures in a file
            with open(self.arch_file_path, "w") as f:
                # Remove duplicates
                for arch in list(set(valid_archs)):  
                    f.write(arch + "\n")
            return valid_archs
        except Exception as e:
            print("An error occurred while trying to retrieve the available architectures: ", e)
            sys.exit(1)
    
    def is_available_arch_older_than(self, days: int) -> bool:
        # Check if the available architectures file is older than the given number of days
        arch_file_path = self.arch_file_path
        if os.path.exists(arch_file_path):
            arch_file_mod_time = os.path.getmtime(arch_file_path)
            if arch_file_mod_time < (time.time() - (days * 24 * 60 * 60)):
                return True
            else:
                return False
        else:
            return True
        

