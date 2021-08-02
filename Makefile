help:
	@echo "Docker Compose Help"
	@echo "-----------------------"
	@echo ""
	@echo "Build the web:"
	@echo "    make build"
	@echo ""
	@echo "Run tests to ensure current state is good:"
	@echo "    make test"
	@echo ""
	@echo "If tests pass,start up the web:"
	@echo "    make start"
	@echo ""
	@echo "Really, really start over:"
	@echo "    make clean"
	@echo ""
	@echo "See contents of Makefile for more targets."

start:
	@docker-compose up -d

stop:
	@docker-compose stop

status:
	@docker-compose ps

restart: stop start

clean: stop
	@docker-compose rm --force
	@find . -name \*.pyc -delete

build:
	@docker-compose build web

flake8:
	@docker-compose run --rm web flake8

test:
	@docker-compose run --rm web python ./manage.py test

migrations:
	@docker-compose run --rm web python ./manage.py makemigrations

migrate:
	@docker-compose run --rm web python ./manage.py migrate

shell:
	@docker-compose run --rm web python ./manage.py shell

superuser:
	@docker-compose run --rm web python ./manage.py createsuperuser

startapp:
	@docker-compose run --rm web python ./manage.py startapp $(appname)

cli:
	@docker-compose run --rm web bash

tail:
	@docker-compose logs -f

.PHONY: start stop status restart clean build flake8 test migrations migrate shell cli tail
