MAKEFILE_PATH := $(abspath $(lastword $(MAKEFILE_LIST)))
PROJECT_DIR := $(notdir $(patsubst %/,%,$(dir $(MAKEFILE_PATH))))
GITHUB_SHA := $(shell git rev-parse HEAD)

install:
	echo "Create virtual env ..."
	poetry lock --no-update && poetry install --sync --no-ansi --no-root

coverage_pytest:
	poetry run coverage run -m pytest
	poetry run coverage report

docker_pytest:
	echo "Run pytest in docker"
	docker build --platform=linux/amd64 -t ${PROJECT_DIR}:test . --target pytest

build_local:
	echo "Build Docker image ${PROJECT_DIR}:local locally"
	docker build --platform=linux/amd64 -t ${PROJECT_DIR}:local .

run_local:
	echo "Run ${PROJECT_DIR}:local locally"
	docker run --env-file .env \
		-v ./logs:/app/logs \
		--rm ${PROJECT_DIR}:local /app/src/main.py
