pipeline {
    agent {
        label "16.04&&ipstudio-deps"
    }
    stages {
        stage ("parallel jobs") {
            parallel {
                stage ("python2.7 unit tests") {
                    agent {
                        label "16.04&&ipstudio-deps"
                    }
                    steps {
                        githubNotify account: 'bbc', credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9', context: "tests/py27", description: 'Python2.7 Tests', repo: 'rd-apmm-python-lib-mediatimestamp', sha: "${sha1}", targetUrl: "${BUILD_URL}", status: 'PENDING'
                        git branch: '${sha1}', credentialsId: '7aa7cd3c-8f60-4e88-bbff-c75516908284', url: 'git@github.com:bbc/rd-apmm-python-lib-mediatimestamp.git'
                        withEnv(['HTTP_PROXY=http://www-cache.rd.bbc.co.uk:8080', 
                                 'HTTPS_PROXY=http://www-cache.rd.bbc.co.uk:8080', 
                                 'no_proxy=mirror.rd.bbc.co.uk,.rd.bbc.co.uk,localhost,127.0.0.1,jenkins.rd.bbc.co.uk', 
                                 'PIP_EXTRA_INDEX_URL=https://artifactory.virt.ch.bbc.co.uk/artifactory/api/pypi/ap-python/simple', 
                                 'PIP_CLIENT_CERT=/etc/pki/tls/private/client_crt_key.pem']) {
                            sh 'tox -e py27'
                        }
                    }
                    post {
                        success {
                            githubNotify account: 'bbc', credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9', context: "tests/py27", description: 'Python2.7 Tests', repo: 'rd-apmm-python-lib-mediatimestamp', sha: "${sha1}", targetUrl: "${BUILD_URL}", status: 'SUCCESS'
                        }
                        failure {
                            githubNotify account: 'bbc', credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9', context: "tests/py27", description: 'Python2.7 Tests', repo: 'rd-apmm-python-lib-mediatimestamp', sha: "${sha1}", targetUrl: "${BUILD_URL}", status: 'FAILURE'
                        }
                    }
                }
                stage ("python3 unit tests") {
                    agent {
                        label "16.04&&ipstudio-deps"
                    }
                    steps {
                        githubNotify account: 'bbc', credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9', context: "tests/py3", description: 'Python3 Tests', repo: 'rd-apmm-python-lib-mediatimestamp', sha: "${sha1}", targetUrl: "${BUILD_URL}", status: 'PENDING'
                        git branch: '${sha1}', credentialsId: '7aa7cd3c-8f60-4e88-bbff-c75516908284', url: 'git@github.com:bbc/rd-apmm-python-lib-mediatimestamp.git'
                        withEnv(['HTTP_PROXY=http://www-cache.rd.bbc.co.uk:8080', 
                                'HTTPS_PROXY=http://www-cache.rd.bbc.co.uk:8080', 
                                'no_proxy=mirror.rd.bbc.co.uk,.rd.bbc.co.uk,localhost,127.0.0.1,jenkins.rd.bbc.co.uk', 
                                'PIP_EXTRA_INDEX_URL=https://artifactory.virt.ch.bbc.co.uk/artifactory/api/pypi/ap-python/simple', 
                                'PIP_CLIENT_CERT=/etc/pki/tls/private/client_crt_key.pem']) {
                            sh 'tox -e py3'
                        }
                    }
                    post {
                        success {
                            githubNotify account: 'bbc', credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9', context: "tests/py3", description: 'Python3 Tests', repo: 'rd-apmm-python-lib-mediatimestamp', sha: "${sha1}", targetUrl: "${BUILD_URL}", status: 'SUCCESS'
                        }
                        failure {
                            githubNotify account: 'bbc', credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9', context: "tests/py3", description: 'Python3 Tests', repo: 'rd-apmm-python-lib-mediatimestamp', sha: "${sha1}", targetUrl: "${BUILD_URL}", status: 'FAILURE'
                        }
                    }
                }
                stage ("debian packaging") {
                    agent {
                        label "16.04&&ipstudio-deps"
                    }
                    steps {
                        githubNotify account: 'bbc', credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9', context: "package/deb", description: 'Package Deb', repo: 'rd-apmm-python-lib-mediatimestamp', sha: "${sha1}", targetUrl: "${BUILD_URL}", status: 'PENDING'
                        git branch: '${sha1}', credentialsId: '7aa7cd3c-8f60-4e88-bbff-c75516908284', url: 'git@github.com:bbc/rd-apmm-python-lib-mediatimestamp.git'
                        sh 'python ./setup.py sdist'
                        sh 'make dsc'
                        sh '''
(
    cd deb_dist/;
    cd `ls|egrep -v "(tar.gz|dsc|orig)"`;
    dch -ljenkins "Jenkins Nightly Build";
    sed -i "s/jenkins1/jenkins${BUILD_NUMBER}~${ENVIRONMENT}~${VCSREV}/" debian/changelog;
    sed -i '/%:/i \\
export PYBUILD_DISABLE=test' debian/rules
    debuild -uc -us -S;
    PKG_NAME=$(head -n 1 debian/control | cut -d " " -f 2);
    rm -fv ${PKG_NAME}_*;
    mv -v ../${PKG_NAME}_* .;

    export DIST=${DIST};
    export ARCH=${ARCH};
    export COMP=${APT_REPO}/${ENVIRONMENT};
    export WKSPRESULT=${WORKSPACE}/_result;

    #these repos are not split into master/stable
    REPO_URL=https://jenkins.rd.bbc.co.uk/repo/${ARCH}/${DIST};
    UBUNTUBACKPORTS="http://gb.archive.ubuntu.com/ubuntu ${DIST}-backports main restricted universe multiverse";

    #these repos *do* have a notion of master/stable;
    PYTHONREPO=$REPO_URL/${APT_REPO}/${ENVIRONMENT};
    BINDMOUNTS="/run/dbus /var/lib/dbus /dev/shm /run/shm";
    CPUS=`grep -c ^processor /proc/cpuinfo`;

    #some rules files examine this to parallelise (boost for example);
    export DEB_BUILD_OPTIONS="parallel=${CPUS} notest nocheck";
    if [ -d ${WKSPRESULT} ]; then
        rm -rf ${WKSPRESULT};
    fi;
    mkdir ${WKSPRESULT};
    sudo -n /usr/sbin/pbuilder --build --configfile /etc/pbuilder/${DIST}-${ARCH}/pbuilderrc --buildresult ${WKSPRESULT} --override-config --othermirror "deb $PYTHONREPO / | deb $UBUNTUBACKPORTS" --bindmounts "${BINDMOUNTS}" --debbuildopts "-j${CPUS}" ${PKG_NAME}_*${VCSREV}.dsc
)
'''
                    }
                    post {
                        success {
                            archiveArtifacts '_result/*'
                            sh '''#!/bin/bash
#if [ "z${sha1}" = "zmaster" ]; then
#    echo "Publishing debian products via ssh"
#    scp _result/* repomgr@jenkins.rd.bbc.co.uk:/var/lib/jenkins/repomgr/queue/
#    ssh repomgr@jenkins.rd.bbc.co.uk "/var/lib/jenkins/repomgr/repo-update ${APT_REPO}/${ENVIRONMENT} ${DIST} ${ARCH} ${BUILD_TAG} || /var/lib/jenkins/repomgr/repo-update ${APT_REPO}/${ENVIRONMENT} ${DIST} ${ARCH} FIX"
#fi
'''
                            githubNotify account: 'bbc', credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9', context: "package/deb", description: 'Package Deb', repo: 'rd-apmm-python-lib-mediatimestamp', sha: "${sha1}", targetUrl: "${BUILD_URL}", status: 'SUCCESS'
                        }
                        failure {
                            githubNotify account: 'bbc', credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9', context: "package/deb", description: 'Package Deb', repo: 'rd-apmm-python-lib-mediatimestamp', sha: "${sha1}", targetUrl: "${BUILD_URL}", status: 'FAILURE'
                        }
                    }
                }
                stage ("rpm packaging") {
                    agent {
                        label "mock-centos7-amd64"
                    }
                    steps {
                        githubNotify account: 'bbc', credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9', context: "package/rpm", description: 'Package RPM', repo: 'rd-apmm-python-lib-mediatimestamp', sha: "${sha1}", targetUrl: "${BUILD_URL}", status: 'PENDING'
                        git branch: '${sha1}', credentialsId: '7aa7cd3c-8f60-4e88-bbff-c75516908284', url: 'git@github.com:bbc/rd-apmm-python-lib-mediatimestamp.git'
                        sh 'python ./setup.py sdist'
                        sh 'rm -rf build/rpm/SOURCES'
                        sh 'rm -rf build/rpm/SPECS'
                        sh 'make rpm_dirs'
                        sh '''#!/bin/bash
set -e

export LD_PRELOAD="${LD_PRELOAD:+$LD_PRELOAD:}/usr/lib/libeatmydata/libeatmydata.so"

# Create a release tag if not set alread
if [ -z $RELEASE ]; then
	GITREV=$(git rev-parse --short origin/master)
	RELEASE=${BUILD_NUMBER}.jenkins.${ENVIRONMENT}.${GITREV}
fi

cd build/rpm
BUILDDIR=${WORKSPACE}/build/rpm

# Cleanup any old RPM packages that survived to this point
rm -rf packages/${OS}-${OS_ARCH}
mkdir -p packages/${OS}-${OS_ARCH}

# Create a mock directory for the mock config to live in
[ ! -d mock ] && mkdir mock

# Set up the build directory permissions so the mock group can write to it, and setgid
chgrp mock $BUILDDIR
chmod 2775 $BUILDDIR

# Munge the mock config to set the base directory to the build folder, and copy locally
if [ -z "$modify_mock_cfg" ]; then
    modify_mock_cfg=\'cat\'
fi

(echo "config_opts[\'basedir\']=\'$BUILDDIR\'"; cat /project-mcuk/jenkins/mock/${OS}-${OS_ARCH}${OS_VARIANT:+-$OS_VARIANT}${target:+-$target}.cfg) | $modify_mock_cfg > mock/default.cfg.new

# Replace the dist macro with our build number definition
# Matches the whole of config_opts[\'macros\'][\'dist\'] = \'something\' up to and excluding the final quote.
# Appends the %{buildnum} macro, which ends up inside the final quote. @ is used as the delimeter.
sed -i \'s@^config_opts\\[[\'\\\'\'"]macros[\'\\\'\'"]\\]\\[[\'\\\'\'"]%dist[\'\\\'\'"]\\] *= *[\'\\\'\'"][^\'\\\'\'"]*@&.%{buildnum}@\' mock/default.cfg.new

# Replace the chroot setup command contents with a macro to insteall the right bits
# Matches the whole of config_opts[\'chroot_setup_cmd\'] = \'something something else\' up to and excluding the final quote.
# Up to and including the first quote after the = is a capture group, which is inserted into the output (\\1) followed by the
# new macro. # is used as the delimeter
sed -i \'s#\\(^config_opts\\[[\'\\\'\'"]chroot_setup_cmd[\'\\\'\'"]\\] *= *[\'\\\'\'"]\\)[^\'\\\'\'"]*#\\1install @buildsys-build#\' mock/default.cfg.new

# Only update the mock config if it differs - we might be able to keep the existing cached chroot
diff -q mock/default.cfg mock/default.cfg.new 2>/dev/null && rm -f mock/default.cfg.new || mv -f mock/default.cfg.new mock/default.cfg
cp -u /etc/mock/site-defaults.cfg /project-mcuk/jenkins/mock/logging.ini mock/

echo \'=== Building... ===\'

# Set up the mock environment
/usr/bin/mock --configdir="$BUILDDIR/mock" --init

# If there were local RPMs to install, install them
if [ -d "localpkgs" ]; then
    /usr/bin/mock --configdir="$BUILDDIR/mock" --no-clean --no-cleanup-after --install "$BUILDDIR/localpkgs/"*.rpm
fi

# If we had a command to run to set up the chroot, run it
if [ -n "$init_chroot_cmd" ]; then
    /usr/bin/mock --configdir="$BUILDDIR/mock" --no-clean --no-cleanup-after --chroot "$init_chroot_cmd"
fi

# If we have some sources, run a source build
if [ -d SOURCES ]; then
    rm -rf ${BUILDDIR}/SRPM
    /usr/bin/mock --configdir=${BUILDDIR}/mock --no-clean --no-cleanup-after --resultdir=${BUILDDIR}/SRPM --buildsrpm --define=\'buildnum \'$RELEASE --spec ${BUILDDIR}/SPECS/*.spec --sources ${BUILDDIR}/SOURCES/
fi
  
# Run a binary build
/usr/bin/mock ${target:+--target=$target} --configdir="$BUILDDIR/mock" --no-clean --define=\'buildnum \'$RELEASE --rebuild "$BUILDDIR/SRPM/"*.src.rpm

# Symlink the results up to the packages directory
ln "$BUILDDIR/${OS}-${OS_ARCH}"/result/*.rpm packages/${OS}-${OS_ARCH}/ || true'''
                    }
                    post {
                        always {
                            archiveArtifacts 'build/rpm/${OS}-${OS_ARCH}/result/*'
                            sh '''#!/bin/bash
set -e

export LD_PRELOAD=/usr/lib/libeatmydata/libeatmydata.so
/usr/bin/mock --configdir="$WORKSPACE/build/rpm/mock" --clean
                            '''
                        }
                        success {
                            githubNotify account: 'bbc', credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9', context: "package/rpm", description: 'Package RPM', repo: 'rd-apmm-python-lib-mediatimestamp', sha: "${sha1}", targetUrl: "${BUILD_URL}", status: 'SUCCESS'
                        }
                        failure {
                            githubNotify account: 'bbc', credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9', context: "package/rpm", description: 'Package RPM', repo: 'rd-apmm-python-lib-mediatimestamp', sha: "${sha1}", targetUrl: "${BUILD_URL}", status: 'FAILURE'
                        }
                    }
                }
            }
            failFast true
        }
    }
}