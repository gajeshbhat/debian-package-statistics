#!/bin/bash

# Check if python3 is installed if not install it using apt
if ! command -v python3 &> /dev/null
then
    echo "python3 could not be found"
    echo "Installing python3"
    sudo apt install python3 python3-pip -y
fi

# Create a venv if does not exist and activate it
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Install the package_statistics application in the current virtualenv
chmod +x package_statistics.py
./package_statistics.py --help