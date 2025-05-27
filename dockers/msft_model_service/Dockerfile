# base image
FROM  nvcr.io/uwsmphrad/florenceinferenceuw:1.0
WORKDIR /workingdir
LABEL authors="ckashuk@wisc.edu"

# uw cert stuff
RUN DEBIAN_FRONTEND=noninteractive apt-get -y update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y ca-certificates wget curl
ADD UWHEALTHROOT.crt /usr/local/share/ca-certificates/UWHEALTHROOT.crt
RUN chmod 644 /usr/local/share/ca-certificates/UWHEALTHROOT.crt && update-ca-certificates

# dependencies
# COPY ./cxr_report_gen_environment.yaml cxr_report_gen_environment.yaml
COPY ./startup.sh startup.sh
RUN chmod +x startup.sh
COPY ./requirements.txt requirements.txt
RUN pip install -r /workingdir/requirements.txt

# prepare and start
# COPY . .
# CMD ["jupyter lab"]
# CMD ["/bin/bash"]
CMD ["./startup.sh"]