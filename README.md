# Canonical Technical Assessment

## Instructions

Debian uses *deb packages to deploy and upgrade software. The packages
are stored in repositories and each repository contains the so called "Contents
index". The format of that file is well described here
https://wiki.debian.org/RepositoryFormat#A.22Contents.22_indices

Your task is to develop a python command line tool that takes the
architecture (amd64, arm64, mips etc.) as an argument and downloads the
compressed Contents file associated with it from a Debian mirror. The
program should parse the file and output the statistics of the top 10
packages that have the most files associated with them.
An example output could be:

./package_statistics.py amd64

1. <package name 1>         <number of files>
2. <package name 2>         <number of files>
......
10. <package name 10>         <number of files>

You can use the following Debian mirror
http://ftp.uk.debian.org/debian/dists/stable/main/. Please do try to
follow Python's best practices in your solution. Hint: there are tools
that can help you verify your code is compliant. In-line comments are
appreciated.

Note: the focus is not to write the perfect Python code, but to see how
you'll approach the problem and how you organize your work.


## Assumptions
The following assumptions were made for this project:
1. The user has python3 installed on their system.
2. The user has an internet connection.
3. When using -m or --mirror, the user is providing a valid Debian mirror uses only one branch (stable, testing, unstable etc). This script does support multiple mirrors but only one branch per mirror. If you submit the same mirror twicce with a different branch, the second branch will not be downloaded and the first branch will be used instead.

## Design, thoughts and implementation

1. I started out with a simple design of the application with a bunch function that would download the Contents file, parse it and return the top 10 packages. I then added a command line interface to the application and added the ability to specify the architecture and the number of top packages to retrieve.
2. I then added the ability to specify a mirror to use. I did this by adding a `mirror` argument to the `get_contents_file` function. I also added a `mirror` argument to the `get_top_packages` function. This allowed me to test the application with different mirrors.
3. I then added the ability to reuse the downloaded Contents file. I saved the Contents file in the `data` directory. I then added a `refresh` argument to the `get_contents_file` function. If the `refresh` argument is set to `True`, the file will be downloaded again. If it is set to `False`, the file will be reused if it exists in the `data` directory.
4. I also added the ability to save parsed Contents files in `package_stats.json` in the arch folder in the `data` directory. The results in the json file will be used unless the `refresh` argument is set to `True`.
6. After the above steps, I took a step back and refactored the code to use classes. I created a `PackageStatistics` class that would handle the downloading, parsing and retrieving of the top packages. 
7. I then added the ability to specify the number of top packages to retrieve. I added a `top` argument to the `get_top_packages` function. This allowed the user to specify the number of top packages to retrieve.
8. I then split the architecture validation and architure names file generation into their own Class. I created a `ArchUtils` class that would handle the validation and generation of the architecture names file.
9. As final touches to features, I added the config and logging modules to the application.
10. Reorganized the argument parsing and command line applicatiuon login into the main package_statistics.py file.

I am not using any 3rd party applications for the core application. The performance could be improved using other packages or using multiprocessing, but I am not using them due to the time constraints and scope of the project.

## Application Installation
Application installation is not necessary to run the application. However, if you want to install the application, you can do so by running the `install.sh` script.

```
bash install.sh
```

### Usage With Installation

Once `package_statistics` is installed, you can run it in one of two ways.

```package_statistics --help```

Or:

```python -m package_statistics --help```

The second version is preferred in places where you would want to *ensure* the right version of python is being used, perhaps with a virtal environment.

### Usage Without Installation

If you want to run `package_statistics` without installation, use the helper file instead.

Either modify permissions to make it executable and use a version of python3 to run it:

```bash
chmod +x package_statistics.py
./package_statistics.py --help
```

Or, you can run it with the python command directly.

```bash
python3 package_statistics.py
```

## The `package_statistics` CLI
The command line interface has a help command that teaches you what you can do with the tool.

```bash
usage: ./package_statistics [-h] [-m MIRROR] [-n TOP] [-r] arch

positional arguments:
  arch                  The architecture for which to retrieve the package statistics

options:
  -h, --help            show this help message and exit
  -m MIRROR, --mirror MIRROR
                        The Debian mirror to use
  -n TOP, --top TOP     The number of top packages to retrieve
  -r, --refresh         Refresh the package statistics by downloading and parsing the Contents file again                                                                                                               
```

## Examples

### Getting `amd64` Statistics

```
$ package_statistics amd64
Top packages by number of files:
1. devel/piglit - 51784 files
2. science/esys-particle - 18015 files
3. libdevel/libboost1.74-dev - 14333 files
4. math/acl2-books - 12668 files
5. golang/golang-1.15-src - 9015 files
6. libdevel/liboce-modeling-dev - 7457 files
7. net/zoneminder - 7002 files
8. libdevel/paraview-dev - 6178 files
9. kernel/linux-headers-5.10.0-20-amd64 - 6162 files
10. kernel/linux-headers-5.10.0-18-amd64 - 6156 files
```

### Development and Time taken
It took me around 45 minutes to draft a simple first implementation of the application. I then spent the rest of the time fixing bugs, adding features and refactoring the code. I spent around `5 hours` on the project with regular weekend breaks.
You can view the git commit log in the repo to see my progress and thought process.

### Learnings from the project and problems
1. Apart from a good refresher of the basics of python, libraries and object oriented programming. I learnt a lot about how debian mirrors are structured and the softwares are distributed.
2. Going through the mirror list https://www.debian.org/mirror/list#complete-list and testing my application with various mirrors helped me impove my application and understand the structure of the mirrors and how some mirrors in some countries dont support certian architectures in the main branch. The architecture validation had to to be dynamic accordingly when the mirror URL is passsed to the application.
3. I was also able to understand about udebs. What they are and how they are used.
4. The further understanding of the problem also helped me understand the limitations of my application. For Example on close examination and testing I noticed that different channels (stable,testing,unstable) have different branches (main) and the application must be able to correctly identify the branch and use it to download the Contents file. 

### Testing

The core functions of `package_statistics` have tests. Use the command below to run the tests. These are only few feature tests and do not cover the entire application.

```
$ python setup.py test

```

## Profiling with `py-spy`

`py-spy` offers a great report for the profiling. Note that `py-spy` needs to be installed separately using `pip`.

#### For Initial Run
```
$ py-spy top -- python package_statistics.py amd64
Total Samples 2000
GIL: 92.00%, Active: 100.00%, Threads: 1

  %Own   %Total  OwnTime  TotalTime  Function (filename)                                                                                              
 60.00%  97.00%    1.20s     2.03s   parse_contents_file (packstats/stats.py)
 11.00%  31.00%   0.300s    0.770s   readline (gzip.py)
  8.00%   9.00%   0.250s    0.270s   read (gzip.py)
  0.00%   0.00%   0.160s    0.160s   readinto (socket.py)
  8.00%  11.00%   0.150s    0.190s   _check_not_closed (_compression.py)
  5.00%   6.00%   0.050s    0.060s   dump (json/__init__.py)
  3.00%   3.00%   0.040s    0.040s   closed (gzip.py)

Press Control-C to quit, or ? for help.

process 1253 ended
```

#### For Subsequent Runs (with cache)
```
$ py-spy top -- python package_statistics.py amd64
Total Samples 10
GIL: 70.00%, Active: 100.00%, Threads: 1

  %Own   %Total  OwnTime  TotalTime  Function (filename)                                                                                              
 40.00%  40.00%   0.040s    0.040s   get_data (<frozen importlib._bootstrap_external>)
 30.00%  80.00%   0.030s    0.080s   <module> (urllib/request.py)
 20.00%  20.00%   0.020s    0.020s   _compile_bytecode (<frozen importlib._bootstrap_external>)
 10.00%  10.00%   0.010s    0.010s   _parse (sre_parse.py)
  0.00%  20.00%   0.000s    0.020s   <module> (logging/__init__.py)
  0.00%  10.00%   0.000s    0.010s   _compile (re.py)
  0.00%  40.00%   0.000s    0.040s   <module> (http/client.py)

Press Control-C to quit, or ? for help.

process 1384 ended
```

