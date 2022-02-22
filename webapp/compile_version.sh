#!/usr/bin/env bash
# Helper shell script to help add the _version file to the containers to get the right version information

# Exit on error
set -e

# Create the source distribution
python setup.py sdist

# Be able to come out
cwd=$(pwd)

# Untar the file
cd dist
recent_tar=$(ls -t *.tar.gz | head -1)
untar=${recent_tar%.tar.gz}  # Will get the output folder name, which is tarball -tar.gz
tar -zxvf $recent_tar

# Loop through all args (container names)
for container in "$@"
do
  docker cp $untar/app/_version.py $container:/var/www/app/_version.py
done

echo "Copied _version.py file to containers $@, please reboot containers for version file to take effect."