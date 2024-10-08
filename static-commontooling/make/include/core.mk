#
# Makefile include file to include standard cloudfit tooling
# Do not include directly, is used by layer.mk

CLEAN_FILES?=
BUILD_TAG?=local

# Set sensible defaults for variables that need to be present before this can be used

ifndef topbuilddir
topbuilddir := $(realpath .)
endif

ifndef topdir
topdir := $(topbuilddir)
$(warning topdir is not set, using $(topbuilddir))
endif

project_root_dir?=$(topdir)
reldir=$(eval reldir := $(shell realpath --relative-to $(project_root_dir) $(topdir)))$(value reldir)

# Include defaults file if it exists
-include $(commontooling_dir)/make/include/defaults.mk

# Set the version of python to use throughout, and set the docker images based on it
DEFAULT_PYTHON_VERSION:=3.10
PYTHON_VERSION?=${DEFAULT_PYTHON_VERSION}
ifneq "${PYTHON_VERSION}" "${DEFAULT_PYTHON_VERSION}"
CLOUDFIT_BASE_LABEL?=python${PYTHON_VERSION}
else
CLOUDFIT_BASE_LABEL?=latest
endif

J2CLI_DOCKER_LABEL?=latest

# Set python pip config location
ifeq "${GITHUB_ACTIONS}" "true"
PIP_CONFIG_FILE?=$(project_root_dir)/.pip.conf
else
PIP_CONFIG_FILE?=/etc/pip.conf
endif

CLOUDFIT_BASE_NAME?=python

J2CLI_DOCKER_CONTAINER?=public.ecr.aws/o4o2s1w1/cloudfit/j2cli

ifeq "${FORGE_CERT}" ""
FORGE_CERT:=$(realpath $(HOME)/.certs/devcert.pem)
endif

# Create simple aliases for running some useful tools
DOCKER?=docker
# --pull supports "always", "missing" (pull from remote if not in the local cache) and "never" (don't pull from remote)
DOCKER_RUN_PULL?=always
DOCKER_RUN?=${DOCKER} run --pull ${DOCKER_RUN_PULL} --rm
J2?=$(DOCKER_RUN) -v $(project_root_dir):/data:ro -w /data/$(reldir) ${J2CLI_DOCKER_CONTAINER}:${J2CLI_DOCKER_LABEL}

# Use docker compose V1 if present, else use the docker plugin for V2
DOCKER_COMPOSE_CMD?=$(shell type docker-compose >/dev/null && echo docker-compose || echo docker compose)


all: ;

include $(commontooling_dir)/make/include/version.mk
-include $(project_root_dir)/commontooling/make/include/initialise_common_tooling.mk

# This target does nothing, but since it is a phony target it will always
# be considered to not be up to date, so anything that depends upon it will
# be rebuilt any time it's needed.
forcerebuild:

# This target is expected to be run when checking out to set up some convenient
# files used for editors and IDEs, it is not required for any of the functional
# parts of the tooling
prepcode:

# clean deletes all files in the variable CLEAN_FILES
clean:
	for FILE in $(CLEAN_FILES); do rm -rf $$FILE; done


# install is used to install the project, however that is done
install:

# source creates a source distribution, whatever that means for the tools in question
source:

# test runs standard tests, whatever that means for the tools in question
test:

# lint runs standard linting, whatever that means for the tools in question
lint:

# push runs a standard push up a repo, whatever that means for the tools in question
push: push-check-changes

# push-check-changes is automatically used to check that there are not uncommitted changes before pushing
push-check-changes:
	@{\
		if ! git diff --quiet HEAD; then\
			echo "ERROR: Local changes exist. Please commit them before uploading. You don't need to push the committed changes.";\
			exit 1;\
		fi;\
	}

# Some automatic targets to create convenient directories sometimes needed for other targets
$(topbuilddir)/dist:
	mkdir -p $@

$(topbuilddir)/.tmp:
	mkdir -p $@

$(topbuilddir)/docs:
	mkdir -p $@

# Target to generate docs index
DOC_FILES = $(shell find $(topbuilddir)/docs/ -type f -name '*.html')
FILTERED_DOC_FILES = $(filter-out $(topbuilddir)/docs/index.html, $(DOC_FILES))
STRIPPED_DOC_FILES = $(patsubst $(topbuilddir)/docs/%,%,$(FILTERED_DOC_FILES))

$(topbuilddir)/docs/index.html: $(topbuilddir)/docs
	rm -f $@
	echo "<html><body>" >> $@
	echo "<h1>$(PROJECT) Documentation</h1><p>" >> $@ && \
	set -f; for docfile in $(STRIPPED_DOC_FILES); do \
		echo "<li><a href=\"./$$docfile\">$$docfile</li>" >> $@ ; \
	done
	echo "</p></body></html>" >> $@

all: help-static-files

help-static-files:
	@echo "make static-files                - Update static commontooling files"
	@echo "make check-static-files          - Check that the current static commontooling files are up to date"

.PHONY: prepcode test lint clean install source all forcerebuild help-title push push-check-changes help-static-files static-files check-static-files $(topbuilddir)/docs/index.html
