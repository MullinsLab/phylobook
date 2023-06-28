FROM python:3.9.10

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ADD . /phylobook
WORKDIR /phylobook
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt -y install wget software-properties-common
#RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt update
RUN apt -y install pkg-config
RUN apt-get -y install libxml2-dev libxmlsec1-dev=1.2.37 libxmlsec1-openssl=1.2.37
RUN apt-get install -y apt-utils vim curl apache2 apache2-utils
RUN apt-get -y install libapache2-mod-wsgi-py3
RUN apt-get -y install python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
RUN apt-get install -y apt-utils vim curl
RUN ln /usr/bin/python3 /usr/bin/python
RUN ln -s /usr/local/lib/python3.9 /usr/local/lib/python3
RUN python manage.py collectstatic --settings=phylobook.settings.static --noinput
ADD ./phylobook.conf /etc/apache2/sites-available/000-default.conf
ADD ./ports.conf /etc/apache2/ports.conf
EXPOSE 8000
CMD ["apache2ctl", "-D", "FOREGROUND"]
