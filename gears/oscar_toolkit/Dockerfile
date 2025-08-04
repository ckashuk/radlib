
# Set base image to python:3.12.3-slim-bookworm using index digest hash to fix version
# This version of python:3.12.3-slim-bookworm has OS: Debian 12 (bookworm) and python: 3.12.3
# FROM --platform=linux/amd64 python@sha256:2be8daddbb82756f7d1f2c7ece706aadcb284bf6ab6d769ea695cc3ed6016743
FROM  nvcr.io/uwsmphrad/oscarstudy/oscartoolkit:10.1

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
    pip3 install flywheel-sdk flywheel-gear-toolkit pyyaml

RUN pip3 --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org install --upgrade protobuf==3.20.1 pip setuptools wheel
RUN pip3 --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org install pylibjpeg albumentations==1.3.1 tables ternausnet torchsummary nibabel==4.0.2 SimpleITK==2.3.1 numpy==1.24 argparse tensorboardX ipyvolume dipy nipype==1.10.0 dicom2nifti==2.6.1 pandas scikit-image scikit-learn joblib matplotlib easydict opencv-python mkl

RUN pip --no-cache-dir --default-timeout=600 --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.ngc.nvidia.com --trusted-host developer.download.nvidia.com --trusted-host download.pytorch.org install torch==2.5.1 torchvision==0.20.1 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu124

RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.ngc.nvidia.com --trusted-host developer.download.nvidia.com install xlrd xlwt xlutils timm monai einops fire pytorch-ignite
RUN pip --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.ngc.nvidia.com --trusted-host developer.download.nvidia.com install --upgrade monai
RUN pip --no-cache-dir --trusted-host pypi.org --trusted-host files.pythonhosted.org --trusted-host pypi.ngc.nvidia.com --trusted-host developer.download.nvidia.com install TotalSegmentator==1.5.7


# Copy run.py script to Flywheel spec path
COPY run.py ${FLYWHEEL}/run.py

# Change permissions to make it executable
RUN chmod a+x ${FLYWHEEL}/run.py

# Configure entrypoint
ENTRYPOINT ["python3", "/flywheel/v0/run.py"]
