# base image
FROM rrs_radsurv
LABEL authors="ckashuk@wisc.edu"

# uw cert stuff
RUN DEBIAN_FRONTEND=noninteractive apt-get -y update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates wget curl
ADD UWHEALTHROOT.crt /usr/local/share/ca-certificates/UWHEALTHROOT.crt
RUN chmod 644 /usr/local/share/ca-certificates/UWHEALTHROOT.crt && update-ca-certificates

# env variable test
ENV RADSERVICE_INPUT_PATH=/in
ENV RADSERVICE_OUTPUT_PATH=/out
ENV RADSERVICE_LOGS_PATH=/logs
ENV RADSERVICE_SCRATCH_PATH=/scratch
ENV RADSERVICE_NAME=rrs_radsurv_service

# package dependencies
COPY ./requirements.txt /app/IDIA/requirements.txt
RUN pip install -r /app/IDIA/requirements.txt

# copies
COPY radservice_app.py /app/IDIA/radservice_app.py
COPY ./radlib /app/IDIA/radlib

# run
WORKDIR /app/IDIA
RUN bash /app/IDIA/bash_requirements.sh
ENTRYPOINT ["python3", "/app/IDIA/radservice_app.py"]
