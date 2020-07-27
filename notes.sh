#!/bin/bash

# The binary cannot run on OSX Catalina because its 32-bit
# For testing, I put it in a docker image

# The docker images didnt come with csh, so I had to install them
yum install csh  # it does tcsh

# OR
apt-get update
apt-get install tcsh

# However, in the CentOS 8 docker image, the binary is SO old and the image is SO new,
# that it is missing the libs needed to even recognize that it can run.

# This can be fixed with a few yum commands

yum install /lib/ld-linux.so.2  # installs glibc32, identified by `file qikprop` on OSX from the "interpreter" information
yum install libgcc_s.so.1  # installs libgcc, identified by the shell trying to run qikprop after the ld-linux.so.2

# Or a few apt-get commands (Jump to after the "But"
apt-get install libc6-i386  # Installs the 32-bit libc files: https://stackoverflow.com/a/49705376/10364409
# OR (smaller payload)
apt-get install -y lib32z1  # https://unix.stackexchange.com/a/12957
# But this is then missing libgcc_s.so.1. SO! What we can do instead (https://superuser.com/a/842107)
dpkg --add-architecture i386
apt-get update
apt-get install -y libgcc1:i386
apt-get install tcsh  # dont forget this.....
# Which will get everything


# QikProp then can run, and does not complain, and then generates it outputs.

# I think a docker file might be the best choice here. DO NOT EVER UPLOAD THE DOCKER IMAGE. EVER.

# Things I want to do (in order, marked by complexity tier:
# * Accept the input file
# ** Copy a skeletal QPlimits file with some basic options the user can set
# *** Copy a bare QPlimits file and fill in ALL of the options a user can set
# *** Accept a raw QPlimits file to overwrite
# *** Accept a raw Similar.CSV file to use inplace of the default one
# **** Establish a job queue and put the job in the queue
# **** Give the user a job id number to fetch their job once its done.
# ** Report to the user how things are running
# * Bundle the output files
#   Includes QPSA.out, QP.out, QP.CSV, QPwarning. Optionally include QPlimits, Similar.CSV/Similar.name, and maaaaayyyybe QPlog (usually empty)
# * Return the output files to the user