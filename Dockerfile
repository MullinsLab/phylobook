FROM ubuntu
ADD . /phylobook
WORKDIR /phylobook
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt -y install wget software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt update
RUN apt -y install pkg-config
RUN apt-get -y install libxml2-dev libxmlsec1-dev libxmlsec1-openssl
RUN apt-get -y install python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
RUN apt-get install -y apt-utils vim curl
RUN ln /usr/bin/python3 /usr/bin/python
EXPOSE 3500
CMD ["./manage.py", "runserver", "0.0.0.0:3500"]