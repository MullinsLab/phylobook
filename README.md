# Phylobook


Install **Docker** on host server:
https://docs.docker.com/get-docker/

**Docker Compose** is an additional tool that is automatically included with Mac and Windows downloads of Docker. However if you are on Linux, you will need to add it manually. You can do this by running the command `sudo pip install docker-compose` after your Docker installation is complete.

## Installation and Configuration
`git clone https://github.com/MullinsLab/phylobook.git`

`cd phylobook`

Create .env by copying .env.TEMPLATE

`cp .env.TEMPLATE .env`

Edit config.env and add your specific settings

`nano .env`

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

---------

## For Developers

Install PyCharm


`git clone https://github.com/MullinsLab/phylobook.git`

Create a project from the source.  Add a virtual environment to the project and install the requirements.txt.

`pip3 install -r requirements.txt`

*Note to  Mac users:  xmlsec, lxml, psycopg2 may require you to install or update Xcode Command Line Tools. 

Edit settings/local.py and fill in PROJECT_PATH (location of project/data files) EMAIL settings for you environment.

Perform initial database migrations

`python3 manage.py migrate --settings=phylobook.settings.prod`

Create super user

`python3 manage.py createsuperuser --settings=phylobook.settings.prod`


Run the server from the terminal

`python3 manage.py runserver 0.0.0.0:3030 --settings=phylobook.settings.local`

----

*Notes for SSO users:  Creating a user, at this point, has to be done at the manage.py shell.  Here is example code for adding externally authenticated users.

`python3 manage.py shell`


`from django.contrib.auth.models import User`				

`user = User(username='user_name')`

`user.set_unusable_password()`

`user.is_staff = False`

`user.is_superuser = False`

`user.save()`
`

