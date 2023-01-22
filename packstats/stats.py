import sys
import os
import gzip
import json
import shutil
from typing import List
from urllib.parse import urlparse
from urllib.request import urlopen
from .utils import ArchUtils,get_config

# TODO: Use singleton pattern
configs = get_config()

class PackageStatistics:
    
    DEFAULT_DATA_DIR_PATH = configs["DEFAULT_DATA_DIR_PATH"]

    def __init__(self, arch: str, mirror_url: str, top_n: int, refresh: bool):
        self.arch = arch
        self.mirror_url = mirror_url
        self.top_packs_count = top_n
        self.refresh = refresh
        
        # Validate Input
        self.check_input_sanity()
        self.validate_mirror_url()

        # Extract the mirror domain as differnt mirriors can support different architectures
        self.mirror_domain = self.get_mirror_domain()
        
        # Validate architecture
        ArchUtils(self.mirror_url).validate_arch(self.arch)

        # Files paths
        self.contents_dir_path = PackageStatistics.DEFAULT_DATA_DIR_PATH + f"{self.mirror_domain}/{self.arch}/"
        self.contents_file_path = self.contents_dir_path + "/Contents.gz"
        self.stats_file_path = self.contents_dir_path + "/packages_stats.json"
        print(self.contents_dir_path, self.contents_file_path, self.stats_file_path)


    def get_mirror_domain(self) -> str:
        return urlparse(self.mirror_url).netloc
    
    def check_input_sanity(self):
        if self.top_packs_count < 1:
            print("The number of packages to be shown should be greater than 0")
            sys.exit(1)

    def validate_mirror_url(self):
        try:
            with urlopen(self.mirror_url) as response:
                response.read()
        except Exception as e:
            print("The mirror URL is not valid or isn't working: ", e)
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
                print("The package statistics file is empty")
                sys.exit(1)
            
            top_packages = dict(sorted(package_stats.items(), key=lambda item: item[1], reverse=True)[:self.top_packs_count])
            return top_packages
        
        except Exception as e:
            print("An error occurred while trying to retrieve the top packages: ", e)
            sys.exit(1)

    def run(self):
        if not os.path.exists(self.stats_file_path) or self.refresh:
            self.download_contents_file()
            self.parse_contents_file()
        top_packages = self.get_top_packages()
        print("Top packages by number of files:")
        for i, (package, files) in enumerate(top_packages.items(), start=1):
            print(f"{i}. {package} - {files} files")
