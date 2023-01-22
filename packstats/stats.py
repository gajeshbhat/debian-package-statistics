import sys
import os
import gzip
import json
import shutil
from typing import List
from urllib.parse import urlparse
from urllib.request import urlopen
from .utils import ArchUtils

class PackageStatistics:
    DEFAULT_MIRROR_URL = "http://ftp.uk.debian.org/debian/dists/stable/main/"
    DEFAULT_TOP_N = 10
    DEFAULT_REFRESH = False
    DEFAULT_ARCH = "all"
    DEFAULT_DATA_DIR_PATH = os.getcwd() + "/data/"

    def __init__(self, arch: str = DEFAULT_ARCH, mirror_url: str = DEFAULT_MIRROR_URL, top_n: int = DEFAULT_TOP_N, refresh: bool = DEFAULT_REFRESH):
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
        contents_file_path = PackageStatistics.DEFAULT_DATA_DIR_PATH + f"{self.mirror_domain}/{self.arch}/"
        
        if not os.path.exists(contents_file_path):
            os.makedirs(contents_file_path, exist_ok=True)
        contents_file_name = PackageStatistics.DEFAULT_DATA_DIR_PATH + f"{self.mirror_domain}/{self.arch}/" + "/Contents.gz"
        
        try:
            with urlopen(contents_url) as response, open(contents_file_name, "wb") as out_file:
                shutil.copyfileobj(response, out_file)
        except Exception as e:
            print("An error occurred while trying to download the Contents file: ", e)
            sys.exit(1)

    def parse_contents_file(self):
        contents_file_path = PackageStatistics.DEFAULT_DATA_DIR_PATH + f"{self.mirror_domain}/{self.arch}/" + "/Contents.gz"
        # Parse the Contents file and return a dictionary with the package name as the key and the number of files associated with the package as the value
        package_dict = {}
        with gzip.open(contents_file_path, 'rb') as buffer:
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
        with open(PackageStatistics.DEFAULT_DATA_DIR_PATH + f"{self.mirror_domain}/{self.arch}/" +  "/packages-stats.json", "w") as f:
            json.dump(package_dict, f)

    def get_top_packages(self):
        try:
            with open(PackageStatistics.DEFAULT_DATA_DIR_PATH + f"{self.mirror_domain}/{self.arch}" +  "/packages-stats.json", "r") as f:
                package_stats = json.load(f)
            top_packages = dict(sorted(package_stats.items(), key=lambda item: item[1], reverse=True)[:self.top_packs_count])
            return top_packages
        except Exception as e:
            print("An error occurred while trying to retrieve the top packages: ", e)
            sys.exit(1)

    def run(self):
        if not os.path.exists(PackageStatistics.DEFAULT_DATA_DIR_PATH + f"{self.mirror_domain}/{self.arch}/packages-stats.json") or self.refresh:
            self.download_contents_file()
            self.parse_contents_file()
        top_packages = self.get_top_packages()
        print("Top packages by number of files:")
        for i, (package, files) in enumerate(top_packages.items(), start=1):
            print(f"{i}. {package} - {files} files")
