import sys
from packstats import main_cli

if __name__ == "__main__":
    if sys.argv and len(sys.argv) > 1:
        arch = sys.argv[1]
        main_cli(arch)
    else:
        print("Please provide the architecture, mirror URL, number of packages to print and refresh flag as arguments")