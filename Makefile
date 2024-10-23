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
		-p 8000:8000 \
		--rm ${PROJECT_DIR}:local

build_push_image:
	echo "Login into ${REGISTRY_NAME}"
	az acr login -n ${REGISTRY_NAME}
	echo "Build and push image to ${REGISTRY_NAME}"
	az acr build -r ${REGISTRY_NAME} -g ${RESOURCE_GROUP} --subscription ${SUBSCRIPTION_ID} -t ${PROJECT_DIR}:latest .

create_sa:
	az ad sp create-for-rbac --name "${PROJECT_DIR}-github" --role contributor \
		--scopes /subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP} \
        --sdk-auth
