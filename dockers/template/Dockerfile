# base image
FROM ubuntu:latest
LABEL authors="ckashuk@wisc.edu"

# uw cert stuff
RUN DEBIAN_FRONTEND=noninteractive apt-get -y update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates wget curl
ADD UWHEALTHROOT.crt /usr/local/share/ca-certificates/UWHEALTHROOT.crt
RUN chmod 644 /usr/local/share/ca-certificates/UWHEALTHROOT.crt && update-ca-certificates

# copies
COPY ./fw /bin
COPY ./Scripts /Scripts

# run
# WORKDIR /Data
ENTRYPOINT ["top", "-b"]