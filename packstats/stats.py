import sys
import os
import gzip
import collections
import json
import urllib.request
import argparse
import time
import shutil

DEFAULT_MIRROR_URL = "http://ftp.uk.debian.org/debian/dists/stable/main/"
DEFAULT_TOP_N = 10
DEFAULT_REFRESH = False
DEFAULT_ARCH = "all"
DEFAULT_CONTENTS_DIR_PATH = os.path.abspath(os.path.join(os.getcwd(), os.pardir))+ "/Contents/"

class PackageStatistics:
    def __init__(self, arch=DEFAULT_ARCH,mirror_url=DEFAULT_MIRROR_URL,top_n=DEFAULT_TOP_N,refresh=DEFAULT_REFRESH):
        # Assign the values to the class variables
        self.arch = arch
        self.mirror_url = mirror_url
        self.top_packs_count = top_n
        self.refresh = refresh
        
        # Validate architecture and mirror urls
        self.validate_arch()
        self.validate_mirror_url()

        # Create the contents directory with arch subdirectory if it doesn't exist
        os.makedirs(DEFAULT_CONTENTS_DIR_PATH +self.arch, exist_ok=True)

        # If the refresh flag is set then delete and update the contents directory and archs.txt file
        if self.refresh:
            self.refresh_arch_data()
            self.refresh_arch_types()

    def refresh_arch_data(self):
        # Delete the contents directory for the given architecture and archs.txt file
        os.remove(DEFAULT_CONTENTS_DIR_PATH + self.arch + "/packages-stats.json")
        os.remove(DEFAULT_CONTENTS_DIR_PATH + self.arch + "Contents.gz")

    def refresh_arch_types(self):
        # Delete the archs.txt file
        os.remove(DEFAULT_CONTENTS_DIR_PATH + "/archs.txt")

    def validate_arch(self):
        if os.path.exists(DEFAULT_CONTENTS_DIR_PATH + "/archs.txt"):
            with open(DEFAULT_CONTENTS_DIR_PATH + "/archs.txt", "r") as f:
                archs = f.read().splitlines()
                if self.arch not in archs:
                    print("The given architecture is not available on the Debian Mirror")
                    sys.exit(1)
                else:
                    return self.arch
        else:
                # Create the archs.txt file if it doesn't exist
                os.makedirs(DEFAULT_CONTENTS_DIR_PATH, exist_ok=True)
                archs = self.create_arch_file(self.mirror_url)
                if self.arch not in archs:
                    print("The given architecture is not available on the Debian Mirror")
                    sys.exit(1)
                else:
                    return self.arch

    def create_arch_file(self,mirror_url=DEFAULT_MIRROR_URL):
        # Create the archs.txt file if it doesn't exist
        os.makedirs(DEFAULT_CONTENTS_DIR_PATH, exist_ok=True)
        try:
            with urllib.request.urlopen(mirror_url) as response:
                raw_html = response.read()
                html = raw_html.decode("utf-8")

            # Find the available architectures
            archs = html.split("Contents-")[1:]
            valid_archs = [arch.split(".gz")[0] for arch in archs]
            
            # Save the available architectures in a file
            with open(DEFAULT_CONTENTS_DIR_PATH + "/archs.txt", "w+") as f:
                for arch in list(set(valid_archs)):
                    f.write(arch + "\n")
            return valid_archs
        except urllib.error.URLError as e:
            print("Network error: " + str(e.reason))
            print("Unable to download the Contents file from the Debian FTP server")
            sys.exit(1)

    def validate_mirror_url(self):
        try:
            mirror_status = urllib.request.urlopen(self.mirror_url).getcode()
            if mirror_status == 200:
                print("Mirror URL is up")
                return True
            else:
                print("Mirror URL is down! Please try a differnt mirror URL")
                return False
        except urllib.error.URLError as e:
            print("Network error: " + str(e.reason))
            print("Unable to download the Contents file from the Debian FTP server")
            sys.exit(1)

    def get_content_url(self, arch,mirror_url):
        return mirror_url + "Contents-" + arch + ".gz"
    
    def download_contents_file(self, arch,mirror_url):
        # Download the Contents file and save it with arch as the name in the contents directory
        try:
            print("Downloading Contents file for architecture " + arch + "...")
            urllib.request.urlretrieve(self.get_content_url(arch,mirror_url), DEFAULT_CONTENTS_DIR_PATH + f"{arch}/Contents.gz")
            print("Contents file downloaded")
            return DEFAULT_CONTENTS_DIR_PATH + f"{arch}/Contents.gz"
        except urllib.error.URLError as e:
            print("Network error: " + str(e.reason))
            print("Unable to download the Contents file from the Debian FTP server")
            sys.exit(1)

    def get_contents_file(self):
        # Check if the Contents file is already downloaded then return the path
        if os.path.exists(DEFAULT_CONTENTS_DIR_PATH+f"{self.arch}/Contents.gz"):
            print("Contents file already downloaded")
            return DEFAULT_CONTENTS_DIR_PATH + f"{self.arch}/Contents.gz"
        else:
            # Download the Contents file and save it with arch as the name in the contents directory
            return self.download_contents_file(self.arch,self.mirror_url)
               
    def parse_contents_file(self, path):
        # Parse the Contents file and return a dictionary with the package name as the key and the number of files associated with the package as the value
        package_dict = {}
        with gzip.open(path, 'rb') as buffer:
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
        return package_dict
    
    def sort_packages_dict(self, packages):
        # Sort the dictionary by the number of files associated with each package in descending order
        packages = collections.OrderedDict(sorted(packages.items(), key=lambda x: x[1], reverse=True))
        return packages
    
    def save_sorted_packages_dict_to_json(self,arch,packages):
        # Save the sorted dictionary to a json file
        with open(DEFAULT_CONTENTS_DIR_PATH + f"{arch}/packages-stats.json", "w+") as f:
            f.write(json.dumps(packages))
        
    def get_sorted_packages_dict_from_json(self,arch):
        # Get the sorted dictionary from a json file
        print(DEFAULT_CONTENTS_DIR_PATH + f"{arch}/package-stats.json")
        with open(DEFAULT_CONTENTS_DIR_PATH + f"{arch}/packages-stats.json", "r") as f:
            packages = json.loads(f.read())
        return packages
    
    def delete_arch_dir(self,arch):
        # Delete the directory for a given architecture
        shutil.rmtree(DEFAULT_CONTENTS_DIR_PATH + f"{arch}")

    def delete_arch_file(self):
        # Delete the file containing the available architectures
        os.remove(DEFAULT_CONTENTS_DIR_PATH + "/archs.txt")

    def gen_new_packstat(self,arch):
        # Generate new package statistics for a given architecture
        contents_file_path = self.get_contents_file()
        packages = self.parse_contents_file(contents_file_path)
        packages = self.sort_packages_dict(packages)
        self.save_sorted_packages_dict_to_json(arch,packages)
        return packages

    def print_top_n_packages(self, n=DEFAULT_TOP_N):
        if os.path.exists(DEFAULT_CONTENTS_DIR_PATH+f"{self.arch}/packages-stats.json"):
            # If the json file exists then check if it was updated in the last 24 hours
            last_modified = os.path.getmtime(DEFAULT_CONTENTS_DIR_PATH+f"{self.arch}/packages-stats.json")
            if time.time() - last_modified < 86400:
                # If it was updated in the last 24 hours then just print the top n packages
                packages = self.get_sorted_packages_dict_from_json(self.arch)
                self.print_top_packages(packages)
                return
            else:
                # If it was not updated in the last 24 hours then refresh the file
                self.delete_arch_dir(self.arch)
                self.delete_arch_file(self)
                packages = self.gen_new_packstat(self.arch)
        else:
             packages = self.gen_new_packstat(self.arch)
        
        self.print_top_packages(packages,n)

    def print_top_packages(self,packages,n=DEFAULT_TOP_N):
        print(f"\t\tTop {n} packages:\n")
        print("\t\tNumber\tPackage\tNumber of files")
        for package in list(packages.keys())[:n]:
            # Print in the format number package_name number_of_files
            print(f"\t\t{list(packages.keys()).index(package)+1}\t{package}\t{packages[package]}")


# Main function
def main_cli(arch=DEFAULT_ARCH, mirror_url=DEFAULT_MIRROR_URL, n=DEFAULT_TOP_N, refresh=DEFAULT_REFRESH):
    top_n_packages = PackageStatistics(arch, mirror_url, n, refresh)
    top_n_packages.print_top_n_packages(n)