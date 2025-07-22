# start with base image
FROM rrs_radsurv

# add radlib stuff
COPY --from=radlib / /

LABEL authors="ckashuk@wisc.edu"

# uw cert stuff
# RUN DEBIAN_FRONTEND=noninteractive apt-get -y update
# RUN DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates wget curl
COPY UWHEALTHROOT.crt /usr/local/share/ca-certificates/UWHEALTHROOT.crt
RUN chmod 644 /usr/local/share/ca-certificates/UWHEALTHROOT.crt && update-ca-certificates

# package dependencies
COPY requirements.txt /app/
RUN pip install -r /app/requirements.txt

WORKDIR /app
COPY ../processor_app.py /app/

# run it!
CMD ["python", "processor_app.py"]
# CMD ["/bin/bash"]