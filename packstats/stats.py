import sys
import os
import gzip
import json
import shutil
import time
from typing import List
from urllib.parse import urlparse
from urllib.request import urlopen

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
        
        # Extract the mirror domain as differnt mirriors can support different architectures
        self.mirror_domain = urlparse(self.mirror_url).netloc

        # Validate architecture and mirror urls
        self.validate_arch()
        self.validate_mirror_url()

    def validate_arch(self):
        # Check if the given architecture is available on the mirror

        # If the available architectures file exists and is not older than 1 day, use it
        if os.path.exists(PackageStatistics.DEFAULT_DATA_DIR_PATH + f"{self.mirror_domain}/available-archs.txt") and not self.is_available_arch_older_than(self.arch, 1):
            with open(PackageStatistics.DEFAULT_DATA_DIR_PATH + f"{self.mirror_domain}/available-archs.txt", "r") as f:
                archs = f.read().splitlines()
                if self.arch not in archs:
                    print("The given architecture is not available on this Debian Mirror")
                    sys.exit(1)
                else:
                    return self.arch
        else:
            # If the available architectures file doesn't exist or is older than 1 day, create it or update it
            os.makedirs(PackageStatistics.DEFAULT_DATA_DIR_PATH + f"{self.mirror_domain}", exist_ok=True)
            archs = self.create_arch_file(self.mirror_url)
            if self.arch not in archs:
                print("The given architecture is not available on the Debian Mirror")
                sys.exit(1)
            else:
                return self.arch
            
    def create_arch_file(self, mirror_url: str = DEFAULT_MIRROR_URL) -> List[str]:
        try:
            with urlopen(mirror_url) as response:
                raw_html = response.read()
                html = raw_html.decode("utf-8")

            # Find the available architectures
            archs = html.split("Contents-")[1:]
            valid_archs = [arch.split(".gz")[0] for arch in archs]

            # Save the available architectures in a file
            with open(PackageStatistics.DEFAULT_DATA_DIR_PATH + f"{self.mirror_domain}/available-archs.txt", "w") as f:
                # Remove duplicates
                for arch in list(set(valid_archs)):  
                    f.write(arch + "\n")
            return valid_archs
        except Exception as e:
            print("An error occurred while trying to retrieve the available architectures: ", e)
            sys.exit(1)

    def is_available_arch_older_than(self, arch: str, days: int) -> bool:
        # Check if the available architectures file is older than the given number of days
        arch_file_path = PackageStatistics.DEFAULT_DATA_DIR_PATH + f"{self.mirror_domain}/available-archs.txt"
        if os.path.exists(arch_file_path):
            arch_file_mod_time = os.path.getmtime(arch_file_path)
            if arch_file_mod_time < (time.time() - (days * 24 * 60 * 60)):
                return True
            else:
                return False
        else:
            return True

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
                # Skip empty lines
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
