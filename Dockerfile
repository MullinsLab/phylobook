FROM python:3.9.10

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ADD . /phylobook
WORKDIR /phylobook
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get -y install wget software-properties-common pkg-config libxml2-dev libxmlsec1-dev=1.2.31-1 \
                            libxmlsec1-openssl=1.2.31-1 apt-utils vim curl python3-pip
RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt
RUN ln /usr/bin/python3 /usr/bin/python
RUN ln -s /usr/local/lib/python3.9 /usr/local/lib/python3
RUN python manage.py collectstatic --settings=phylobook.settings.static --noinput
ADD ./phylobook.conf /etc/apache2/sites-available/000-default.conf
ADD ./ports.conf /etc/apache2/ports.conf
EXPOSE 8000


# Install the Phylobook Pipeline

# Install Python stuff
RUN pip install --upgrade pip
RUN pip install -r /phylobook/phylobook_pipeline/requirements.txt

# Install Image-Magick
RUN apt-get -y update
RUN apt-get -y install imagemagick

# Overwrite /etc/ImageMagick-6/policy.xml
RUN mv /etc/ImageMagick-6/policy.xml /etc/ImageMagick-6/policy.xml.bak
RUN cp /phylobook/phylobook_pipeline/policy.xml /etc/ImageMagick-6/policy.xml

# Install Java
RUN apt update
RUN apt -y install default-jre
