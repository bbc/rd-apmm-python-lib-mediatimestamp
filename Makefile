PYTHON=`which python`
PYTHON2=`which python2`
PYTHON3=`which python3`
PY2DSC=`which py2dsc`

topdir := $(realpath $(dir $(lastword $(MAKEFILE_LIST))))
topbuilddir := $(realpath .)

DESTDIR=/
PROJECT=$(shell python $(topdir)/setup.py --name)
VERSION=$(shell python $(topdir)/setup.py --version)
MODNAME=$(PROJECT)
DEBNAME=$(shell echo $(MODNAME) | tr '[:upper:]_' '[:lower:]-')

DEBIANDIR=$(topbuilddir)/deb_dist/$(DEBNAME)-$(VERSION)/debian
DEBIANOVERRIDES=$(patsubst $(topdir)/debian/%,$(DEBIANDIR)/%,$(wildcard $(topdir)/debian/*))

RPMDIRS=BUILD BUILDROOT RPMS SOURCES SPECS SRPMS
RPMBUILDDIRS=$(patsubst %, $(topdir)/build/rpm/%, $(RPMDIRS))

all:
	@echo "$(PROJECT)-$(VERSION)"
	@echo "make source  - Create source package"
	@echo "make install - Install on local system (only during development)"
	@echo "make clean   - Get rid of scratch and byte files"
	@echo "make test    - Test using tox and nose2"
	@echo "make deb     - Create deb package"
	@echo "make rpm     - Create rpm package"
	@echo "make wheel   - Create whl package"
	@echo "make egg     - Create egg package"

$(topbuilddir)/dist:
	mkdir -p $@

source: $(topbuilddir)/dist
	$(PYTHON) $(topdir)/setup.py sdist $(COMPILE) --dist-dir=$(topbuilddir)/dist

$(topbuilddir)/dist/$(MODNAME)-$(VERSION).tar.gz: source

install:
	$(PYTHON) $(topdir)/setup.py install --root $(DESTDIR) $(COMPILE)

clean:
	$(PYTHON) $(topdir)/setup.py clean || true
	rm -rf $(topbuilddir)/.tox
	rm -rf $(topbuilddir)/build/ MANIFEST
	rm -rf $(topbuilddir)/dist
	rm -rf $(topbuilddir)/deb_dist
	rm -rf $(topbuilddir)/*.egg-info
	find $(topdir) -name '*.pyc' -delete
	find $(topdir) -name '*.py,cover' -delete

test:
	tox

deb_dist: $(topbuilddir)/dist/$(MODNAME)-$(VERSION).tar.gz
	$(PY2DSC) --with-python2=true --with-python3=true $(topbuilddir)/dist/$(MODNAME)-$(VERSION).tar.gz

$(DEBIANDIR)/%: $(topdir)/debian/% deb_dist
	cp $< $@

dsc: deb_dist $(DEBIANOVERRIDES)
	cp $(topbuilddir)/deb_dist/$(DEBNAME)_$(VERSION)-1.dsc $(topbuilddir)/dist

deb: source deb_dist $(DEBIANOVERRIDES)
	cd $(DEBIANDIR)/..;debuild -uc -us
	cp $(topbuilddir)/deb_dist/python*$(DEBNAME)_$(VERSION)-1*.deb $(topbuilddir)/dist

# START OF RPM SPEC RULES
# If you have your own rpm spec file to use you'll need to disable these rules
$(topdir)/rpm/$(MODNAME).spec: rpm_spec

rpm_spec: $(topdir)/setup.py
	$(PYTHON3) $(topdir)/setup.py bdist_rpm --spec-only --dist-dir=$(topdir)/rpm
# END OF RPM SPEC RULES

$(RPMBUILDDIRS):
	mkdir -p $@

$(topbuilddir)/build/rpm/SPECS/$(MODNAME).spec: $(topdir)/rpm/$(MODNAME).spec $(topbuilddir)/build/rpm/SPECS
	cp $< $@

$(topbuilddir)/build/rpm/SOURCES/$(MODNAME)-$(VERSION).tar.gz: $(topbuilddir)/dist/$(MODNAME)-$(VERSION).tar.gz $(topbuilddir)/build/rpm/SOURCES
	cp $< $@

rpm: $(topbuilddir)/build/rpm/SPECS/$(MODNAME).spec $(topbuilddir)/build/rpm/SOURCES/$(MODNAME)-$(VERSION).tar.gz $(RPMBUILDDIRS)
	rpmbuild -ba --define '_topdir $(topbuilddir)/build/rpm' --clean $<
	cp $(topbuilddir)/build/rpm/RPMS/*/*.rpm $(topbuilddir)/dist

wheel:
	$(PYTHON2) $(topdir)/setup.py bdist_wheel
	$(PYTHON3) $(topdir)/setup.py bdist_wheel

egg:
	$(PYTHON2) $(topdir)/setup.py bdist_egg
	$(PYTHON3) $(topdir)/setup.py bdist_egg

.PHONY: test test2 test3 clean install source deb dsc rpm wheel egg all
