#!/usr/bin/env python3
import sys
import os
import gzip
import urllib.request
import collections

def check_args():
    # Check if the user has provided an argument
    # Switch to kwargs or use argparse to make it more flexible
    if len(sys.argv) < 2:
        print("Usage: ./package_statistics.py <architecture>")
        sys.exit(1)
    else:
        return sys.argv[1]

def check_arch(arch):
    # Check if the user has provided a valid architecture
    # Check the architecture against a list of valid architectures from the Debian repository, Maintian a list and update every time a new architecture is added
    if arch not in ["amd64", "arm64", "mips", "mipsel", "ppc64el", "s390x"]:
        print("Invalid architecture")
        sys.exit(1)
    else:
        return arch

def download_contents(arch):
    # Download the Contents file and save it with arch as the name in a separate directory
    # Check if the directory exists, if not create it
    # Check the time of the last update of the Contents file and download it only if it is newer than the one in the directory or six hours have passed since the last update
    print("Downloading Contents file...")
    url = "http://ftp.uk.debian.org/debian/dists/stable/main/Contents-" + arch + ".gz"
    urllib.request.urlretrieve(url, "Contents.gz")


def get_file_contents(path):
    # Read the Contents file and save the packages in a dictionary
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

def sort_packages_dict(packages):
    # Sort the dictionary by the number of files associated with each package in descending order
    packages = collections.OrderedDict(sorted(packages.items(), key=lambda x: x[1], reverse=True))
    return packages

def print_top_10_packages(packages):
    # Print the top 10 packages and save them in a separate file and retrive them if not updated in the last 24 hours
    print("Top 10 packages:")
    for package in list(packages.keys())[:10]:
        print(str(package).rsplit('/', 1)[-1] + " " + str(packages[package]))


def delete_file(path):
    # Delete the Contents file
    print("Deleting Contents file...")
    os.remove(path)


def main():
    arch = check_args()
    arch = check_arch(arch)
    download_contents(arch)
    packages = get_file_contents("Contents.gz")
    packages = sort_packages_dict(packages)
    print_top_10_packages(packages)
    delete_file("Contents.gz")

if __name__ == "__main__":
    main()