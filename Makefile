.ONESHELL:
SHELL := /bin/bash
SRC = $(wildcard ./*.ipynb)

all: proseflow docs

proseflow: $(SRC)
	poetry run nbdev_build_lib
	touch proseflow
    
build:
	poetry run nbdev_build_lib

sync:
	poetry run nbdev_update_lib

docs_serve: docs
	cd docs && bundle exec jekyll serve

docs: $(SRC)
	poetry run nbdev_build_docs
	touch docs

test:
	poetry run nbdev_test_nbs

release: pypi
	poetry run nbdev_conda_package
	poetry run nbdev_bump_version

pypi: dist
	poetry run twine upload --repository pypi dist/*
    
gemfury: dist
	poetry run twine upload --repository-url https://push.fury.io/scify -u $GEMFURY_TOKEN -p dist/*
    
version:
    # make version VERSION=patch
	poetry version $(VERSION)

dist: clean
	poetry build

clean:
	rm -rf dist
    
kernel:
	poetry run python -m ipykernel install --user --name proseflow