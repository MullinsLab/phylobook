# Phylobook

Notes before full documentation:

Install **Docker** on host server:
https://docs.docker.com/get-docker/

**Docker Compose** is an additional tool that is automatically included with Mac and Windows downloads of Docker. However if you are on Linux, you will need to add it manually. You can do this by running the command `sudo pip install docker-compose` after your Docker installation is complete.

## Configuration

`docker-compose exec web python manage.py makemigrations`
`docker-compose exec web python manage.py migrate`
`docker-compose exec web python manage.py createsuperuser`
