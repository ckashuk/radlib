# base image
FROM python:3.12.3-slim-bookworm
LABEL authors="ckashuk@wisc.edu"

# uw cert stuff
RUN DEBIAN_FRONTEND=noninteractive apt-get -y update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates wget curl
ADD UWHEALTHROOT.crt /usr/local/share/ca-certificates/UWHEALTHROOT.crt
RUN chmod 644 /usr/local/share/ca-certificates/UWHEALTHROOT.crt && update-ca-certificates

# env variable test
ENV RADSERVICE_INPUT_PATH /in
ENV RADSERVICE_OUTPUT_PATH /out
ENV RADSERVICE_LOGS_PATH /logs
ENV RADSERVICE_SCRATCH_PATH /scratch
ENV RADSERVICE_NAME radservice_name

# package dependencies
COPY ./requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# copies
COPY ./app.py /app/app.py
COPY ./radlib /app/radlib

# COPY ./Scripts /Scripts

# run
WORKDIR /app
# RUN bash
ENTRYPOINT ["python3", "app.py"]
