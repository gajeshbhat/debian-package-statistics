from packstats import PackageStatistics
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("arch", type=str, default=PackageStatistics.DEFAULT_ARCH, help="The architecture for which to retrieve the package statistics")
    parser.add_argument("-m", "--mirror", type=str, default=PackageStatistics.DEFAULT_MIRROR_URL, help="The Debian mirror to use")
    parser.add_argument("-n", "--top", type=int, default=PackageStatistics.DEFAULT_TOP_N, help="The number of top packages to retrieve")
    parser.add_argument("-r", "--refresh", action="store_true", help="Refresh the package statistics by downloading and parsing the Contents file again")
    args = parser.parse_args()
    package_stats = PackageStatistics(arch=args.arch, mirror_url=args.mirror, top_n=args.top, refresh=args.refresh)
    package_stats.run()