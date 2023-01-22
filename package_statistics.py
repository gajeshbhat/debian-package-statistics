import sys
import os
import gzip
import urllib.request
import collections
import json

class PackageStatistics:
    def __init__(self, arch="all",mirror_url="http://ftp.uk.debian.org/debian/dists/stable/main/",top_n=10,refresh=False):
        self.arch = arch
        self.mirror_url = mirror_url
        self.check_arch()
        
        # If the refresh flag is set then delete the contents directory for the given architecture and archs.txt file
        if refresh:
            print("Refreshing the contents directory for the given architecture")
            os.remove(f"Contents/{self.arch}/packages-stats.json")
            os.remove(f"Contents/{self.arch}/Contents.gz")
            os.remove("Contents/archs.txt")
            self.check_arch() # Check the architecture again to download the Contents file and archs.txt file again

        if os.path.exists(f"Contents/{self.arch}/package-stats.json"):
            print("Package statistics already computed")
            self.packages = self.get_sorted_packages_dict_from_json(self.arch)
        else:
            self.content_urls = self.get_content_url(self.arch,self.mirror_url)
            self.contents_file_path = self.get_contents_file(self.content_urls)
            self.packages = self.parse_contents_file(self.contents_file_path)
            self.packages = self.sort_packages_dict(self.packages)
            self.save_sorted_packages_dict_to_json(self.arch,self.packages)

        self.print_top_n_packages(self.packages,top_n)

    def get_content_url(self, arch,mirror_url):
        # Check if the mirror url is a valid mirror url
        return mirror_url + "Contents-" + arch + ".gz"

    def check_arch(self):
        # Check if the architecture list is already downloaded then read from the file anc check if the given architecture is available
        if os.path.exists("Contents/archs.txt"):
            with open("Contents/archs.txt", "r") as f:
                archs = f.read().splitlines()
            if self.arch not in archs:
                print("The given architecture is not available on the Debian FTP server")
                sys.exit(1)
            else:
                return self.arch
        else:
            # If the architecture list is not downloaded then download it and check if the given architecture is available
            os. makedirs("Contents", exist_ok=True)
            try:
                with urllib.request.urlopen("http://ftp.uk.debian.org/debian/dists/stable/main/") as response:
                    raw_html = response.read()
                html = raw_html.decode("utf-8")

                # Find the available architectures
                archs = html.split("Contents-")[1:]
                archs = [arch.split(".gz")[0] for arch in archs]
          
                # Save the available architectures in a file
                with open("Contents/archs.txt", "w+") as f:
                    for arch in list(set(archs)):
                        f.write(arch + "\n")
            
                if self.arch not in archs:
                    print("The given architecture is not available on the Debian FTP server")
                    sys.exit(1)
                else:
                    return self.arch
            except urllib.error.URLError as e:
                print("Network error: " + str(e.reason))
                print("Unable to download the Contents file from the Debian FTP server")
                sys.exit(1)
        
    def get_contents_file(self,url):
        # Check if the Contents file is already downloaded then return the path
        if os.path.exists(f"Contents/{self.arch}/Contents.gz"):
            print("Contents file already downloaded")
            return f"Contents/{self.arch}/Contents.gz"
        else:
            # Download the Contents file and save it with arch as the name in the contents directory
            try:
                print("Downloading Contents file for architecture " + self.arch + "...")
                os.makedirs(f"Contents/{self.arch}", exist_ok=True)
                urllib.request.urlretrieve(url, f"Contents/{self.arch}/Contents.gz")
                print("Contents file downloaded")
                return f"Contents/{self.arch}/Contents.gz"
                # Network error handling
            except urllib.error.URLError as e:
                print("Network error: " + str(e.reason))
                print("Unable to download the Contents file from the Debian FTP server")
                sys.exit(1)
               
    
    def parse_contents_file(self, path):
        # Parse the Contents file and return a dictionary with the package name as the key and the number of files associated with the package as the value
        # Refactor the code below
        package_dict = {}
        with gzip.open(path, 'rb') as buffer:
            for line in buffer:
                line = line.decode("utf-8").strip()
                if line == "":
                    continue
                file_name, packages = line.rsplit(" ", maxsplit=1)
                packages = packages.split(",")
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
        with open(f"Contents/{arch}/packages-stats.json", "w+") as f:
            f.write(json.dumps(packages))
        
    def get_sorted_packages_dict_from_json(self,arch):
        # Get the sorted dictionary from a json file
        print(f"Contents/{arch}/package-stats.json")
        with open(f"Contents/{arch}/packages-stats.json", "r") as f:
            packages = json.loads(f.read())
        return packages

    def print_top_n_packages(self, packages, n):
        # Print the top 10 packages and save them in a separate file and retrive them if not updated in the last 24 hours
        print(f"Top {n} packages:")
        for package in list(packages.keys())[:n]:
            print(str(package).rsplit('/', 1)[-1] + " " + str(packages[package]))


def main():
    if len(sys.argv) != 2:
        print("Usage: package_statistics.py <architecture>")
        sys.exit(1)
    else:
        arch = sys.argv[1]
        PackageStatistics(arch)

if __name__ == "__main__":
    main()