
# Set base image to python:3.12.3-slim-bookworm using index digest hash to fix version
# This version of python:3.12.3-slim-bookworm has OS: Debian 12 (bookworm) and python: 3.12.3
# FROM --platform=linux/amd64 python@sha256:2be8daddbb82756f7d1f2c7ece706aadcb284bf6ab6d769ea695cc3ed6016743
FROM python:3.12.3-slim-bookworm

# Flywheel spec (v0)
ENV FLYWHEEL=/flywheel/v0
RUN mkdir -p ${FLYWHEEL}

# Set the working directory
# Note: This is the directory where the gear is run
WORKDIR ${FLYWHEEL}

# 1. Update package list for apt-get
# 2. Use apt-get to install git package, 
#    skipping installation of recommended packages
#    (to keep the image size small)
# 3. Use pip3 to install the flywheel-sdk package
# Note: git is not required for this gear, but it is included 
# as an example of how to install additional package using
# apt-get
RUN apt-get update -qq && \
    apt-get install --no-install-recommends -y git && \
    pip3 install flywheel-sdk flywheel-gear-toolkit

# Copy run.py script to Flywheel spec path
COPY run.py ${FLYWHEEL}/run.py
# TODO: 202503 csk try to incorporate radlib! but too much now
# COPY /mnt/DGXUserData/cxk023/radlib/radlib/* ${FLYWHEEL}/radlib

# Change permissions to make it executable
RUN chmod a+x ${FLYWHEEL}/run.py

# Configure entrypoint
ENTRYPOINT ["python3", "/flywheel/v0/run.py"]
