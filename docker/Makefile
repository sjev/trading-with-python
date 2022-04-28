.PHONY: build launch push shell

SHELL := /bin/bash

DOCKERFILE=Dockerfile
IMG=sjev/python-dev

USER_UID := $(shell id -u)
USER_GID := $(shell id -g)

build:
	docker build -t $(IMG) -f $(DOCKERFILE) --build-arg USER_UID=$(USER_UID) --build-arg USER_GID=$(USER_GID) .

launch: build
	docker run -it -p 8888:8888 $(IMG)

push: build
	docker push $(IMG)

shell: build
	docker run -it $(IMG) bash