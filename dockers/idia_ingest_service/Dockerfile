# base image
FROM python:3.12.3-slim-bookworm
LABEL authors="ckashuk@wisc.edu"

# uw cert stuff
RUN DEBIAN_FRONTEND=noninteractive apt-get -y update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates wget curl
ADD UWHEALTHROOT.crt /usr/local/share/ca-certificates/UWHEALTHROOT.crt
RUN chmod 644 /usr/local/share/ca-certificates/UWHEALTHROOT.crt && update-ca-certificates

# package dependencies
COPY ./radlab/dockers/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# copies
COPY ./radlab/dockers/radservice_app.py /app/radservice_app.py
COPY ./radlib /app/radlib

# run
WORKDIR /app
# RUN bash
ENTRYPOINT ["python3", "/app/radservice_app.py"]
