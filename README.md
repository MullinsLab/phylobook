# Phylobook


Install **Docker** on host server:
https://docs.docker.com/get-docker/

**Docker Compose** is an additional tool that is automatically included with Mac and Windows downloads of Docker. However if you are on Linux, you will need to add it manually. You can do this by running the command `sudo pip install docker-compose` after your Docker installation is complete.

## Installation and Configuration
`git clone https://github.com/MullinsLab/phylobook.git`

`cd phylobook`

Create config.env by copying config.env.TEMPLATE

`cp config.env.TEMPLATE config.env`

Edit config.env and add your specific settings

`nano config.env`

If you chose LOGIN_TYPE=sso or LOGIN_TYPE=dual in config.env, then you must create settings/saml.py by copying settings/saml.py.TEMPLATE

`cp settings/saml.py.TEMPLATE settings/saml.py`

Edit settings/saml.py and add your institution's SAML configuration and certificates

`nano settings/saml.py`

Build and deploy the containers

`docker-compose up -d --build`

Perform initial database migrations

`docker exec -it phylobook python manage.py migrate --settings=phylobook.settings.prod`

Create super user

`docker exec -it phylobook python manage.py createsuperuser --settings=phylobook.settings.prod`



