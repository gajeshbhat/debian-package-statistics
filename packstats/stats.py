import sys
import os
import gzip
import json
import shutil
from typing import List
from urllib.parse import urlparse
from urllib.request import urlopen
from .utils import ArchUtils,Config
from .utils import Logger

config = Config.instance()

class PackageStatistics:
    
    DEFAULT_DATA_DIR_PATH = config["DEFAULT_DATA_DIR_PATH"]
    LOG_FILE_PATH = config["DEFAULT_LOG_DIR_PATH"] + "packstats.log"

    def __init__(self, arch: str, mirror_url: str, top_n: int, refresh: bool):
        self.logger = Logger(PackageStatistics.LOG_FILE_PATH)
        self.arch = arch
        self.mirror_url = mirror_url
        self.top_packs_count = top_n
        self.refresh = refresh
        
        self.logger.log_info("Initializing PackageStatistics object with the following parameters:")
        self.logger.log_info(f"Architecture: {self.arch}\tMirror URL: {self.mirror_url}\tTop N packages: {self.top_packs_count}\tRefresh: {self.refresh}")

        # Validate Input (top_n,mirror_url)
        self.logger.log_info("Validating input")
        self.check_input_sanity()
        self.validate_mirror_url()

        # Extract the mirror domain as differnt mirriors can support different architectures
        self.mirror_domain = self.get_mirror_domain()
        
        # Validate architecture
        ArchUtils(self.mirror_url).validate_and_create_archs(self.arch)

        # Files paths
        self.contents_dir_path = PackageStatistics.DEFAULT_DATA_DIR_PATH + f"{self.mirror_domain}/{self.arch}/"
        self.contents_file_path = self.contents_dir_path + "/Contents.gz"
        self.stats_file_path = self.contents_dir_path + "/packages_stats.json"


    def get_mirror_domain(self) -> str:
        # Extract the mirror domain as differnt mirriors can support different architectures
        self.logger.log_info(f"Extracting mirror domain from {self.mirror_url}")
        try:
            mirror_domain = urlparse(self.mirror_url).netloc
            self.logger.log_info(f"Mirror domain is {mirror_domain}")
            return mirror_domain
        except Exception as e:
            print("An error occurred while trying to extract the mirror domain! Please enter a differnt URL ")
            self.logger.log_error("An error occurred while trying to extract the mirror domain: ", e)
            sys.exit(1)
    
    def check_input_sanity(self):
        if self.top_packs_count < 1:
            print("The number of packages to be shown should be greater than 0")
            self.logger.log_error("The number of packages to be shown should be greater than 0. User input: ", self.top_packs_count)
            sys.exit(1)

    def validate_mirror_url(self):
        self.logger.log_info(f"Validating mirror URL {self.mirror_url}")
        try:
            with urlopen(self.mirror_url) as response:
                response.read()
            self.logger.log_info("Mirror URL is valid")
        except Exception as e:
            print("The mirror URL is not valid or isn't working. Please enter a differnt URL ")
            self.logger.log_error("The mirror URL is not valid or isn't working: ", e)
            sys.exit(1)

    def download_contents_file(self):
        contents_url = self.mirror_url + f"Contents-{self.arch}.gz"
        
        contents_dir_path = self.contents_dir_path
        if not os.path.exists(contents_dir_path):
            os.makedirs(contents_dir_path, exist_ok=True)
        
        contents_file_path = self.contents_file_path
        try:
            with urlopen(contents_url) as response, open(contents_file_path, "wb") as out_file:
                shutil.copyfileobj(response, out_file)
        except Exception as e:
            print("An error occurred while trying to download the Contents file: ", e)
            sys.exit(1)

    def parse_contents_file(self):
        # Parse the Contents file and return a dictionary with the package name as the key and the number of files associated with the package as the value
        package_dict = {}
        with gzip.open(self.contents_file_path, 'rb') as buffer:
            for line in buffer:
                line = line.decode("utf-8").strip()
                if line == "":
                    continue
                # Split the line into file name and packages
                file_name, packages = line.rsplit(" ", maxsplit=1)
                packages = packages.split(",")
                # For every package in the packages list for a given file add a counter to the dictionary entry for that package
                for package in packages:
                    if file_name != "EMPTY_PACKAGE":
                        if package not in package_dict:
                            package_dict[package] = 1
                        else:
                            package_dict[package] = package_dict[package] + 1
        # Save the dictionary to a json file
        with open(self.stats_file_path, "w+") as f:
            json.dump(package_dict, f)

    def get_top_packages(self):
        try:
            with open(self.stats_file_path, "r") as f:
                package_stats = json.load(f)
            if package_stats is None or package_stats == {}:
                self.logger.log_error("The package statistics file is empty! Please check the mirror URL and architecture")
                print("The package statistics file is empty! No Stats to show!")
                sys.exit(1)
            top_packages = dict(sorted(package_stats.items(), key=lambda item: item[1], reverse=True)[:self.top_packs_count])
            return top_packages
        except Exception as e:
            self.logger.log_error("An error occurred while trying to retrieve the top packages: File does not exisist! ", e)
            print("An error occurred while trying to retrieve the top packages: ")
            sys.exit(1)

    def run(self):
        # Check if the stats file exists and if it doesn't download the contents file and parse it
        self.logger.log_info("Checking if the stats file exists")
        if not os.path.exists(self.stats_file_path) or self.refresh:
            self.logger.log_info("Stats file doesn't exist or refresh is set to True. Downloading the Contents file")
            self.download_contents_file()
            self.logger.log_info("Parsing the Contents file")
            self.parse_contents_file()
        self.logger.log_info("Retrieving the top packages")
        top_packages = self.get_top_packages()
        self.logger.log_info(f"Top packages: {top_packages}")

        print("Top packages by number of files:")
        for i, (package, files) in enumerate(top_packages.items(), start=1):
            print(f"{i}. {package} - {files} files")
