import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="gajeshbhat",
    version="0.1",
    author="Gajesh Bhat",
    author_email="gajeshbht@gmail.com",
    description="A CLI tool to get statistics about packages in a given architecture from Debian mirrors",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    entry_points={
    'console_scripts': [
        'packstats=packstats.package_statistics:run_cli',
    ],
},
)
