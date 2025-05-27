# base image
FROM wasserth/totalsegmentator:2.8.0
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
ENV RADSERVICE_NAME total_segmentator_service

# package dependencies
COPY ./requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt

# copies
COPY radservice_app.py /app/radservice_app.py
COPY ./radlib /app/radlib

# run
WORKDIR /app
# RUN bash
# ENTRYPOINT ["python3", "/app/radservice_app.py"]
