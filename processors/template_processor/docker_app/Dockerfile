# start with base image
FROM radlib

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

# add the script so radservice_app.py knows where to get it
# now adding script_name as a volume!
WORKDIR /app
COPY ../radservice_app.py /app/
# COPY script3.yaml /app/

# run it!
CMD ["python", "radservice_app.py"]
# CMD ["/bin/bash"]