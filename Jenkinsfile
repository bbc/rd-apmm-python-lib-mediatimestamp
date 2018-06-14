/*
 Pipeline for python libraries.

 Can perform the following steps:

 LINT:
   * Uses flake8 to lint the python code
   * Runs only if variable "LINT" is set to "true"

 TEST_PY27:
   * Uses tox to test in python 2.7
   * Runs only if variable "TEST_PY27" is set to "true"

 TEST_PY3:
   * Uses tox to test in python 3
   * Runs only if variable "TEST_PY3" is set to "true"

 BUILD_DEB:
   * Uses py2dsc and pbuilder to build a debian package
   * Runs only if variable "BUILD_DEB" is set to "true"
   * Requires "ENVIRONMENT" variable set to "master", "stable" or similar
   * Requires "APT_REPO" variable set to address of apt repo to retrieve prereqs from
   * Requires "DEB_DIST" variable set to a debian/ubuntu dist name
  
 UPLOAD_TO_ARTIFACTORY:
   * Uses twine to upload a source tarball and two wheels to artifactory
   * Runs only if "UPLOAD_TO_ARTIFACTORY" is "true", "sha1" is "master", and all build and test steps succeeded
   * Requires "ARTIFACTORY_REPO" be set to the address of the artifactory repo

  UPLOAD_DEB:
    * Uses ssh to publish the deb package to our apt repo
    * Runs only if "UPLOAD_DEB" is "true", "BUILD_DEB" is "true", "sha1" is "master", and all build and test steps succeeded
    * Requires the same variables as BUILD_DEB and also "ARCH" which is usually set to amd64 or armhf
*/

pipeline {
    agent {
        label "16.04&&ipstudio-deps"
    }
    stages {
        stage ("parallel jobs") {
            parallel {
                stage ("Linting Check") {
                    when {
                        environment name: "LINT", value: "true"
                    }
                    steps {
                        dir ("lint") {
                            githubNotify (
                                account: "${GITHUBUSER}",
                                credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9',
                                context: "lint/flake8",
                                description: 'Flake8 linting',
                                repo: "${GITREPO}",
                                sha: "${ghprbActualCommit}",
                                targetUrl: "${BUILD_URL}",
                                status: 'PENDING')
                            checkout([$class: 'GitSCM', branches: [[name: '${sha1}']],
                                      doGenerateSubmoduleConfigurations: false,
                                      extensions: [],
                                      submoduleCfg: [],
                                      userRemoteConfigs: [[credentialsId: '7aa7cd3c-8f60-4e88-bbff-c75516908284',
                                                           refspec: '+refs/pull/*:refs/remotes/origin/pr/*',
                                                           url: 'git@github.com:${GITHUBUSER}/${GITREPO}.git']]])
                            sh 'flake8'
                        }
                    }
                    post {
                        success {
                            githubNotify (
                                account: 'bbc',
                                credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9',
                                context: "lint/flake8",
                                description: 'Flake8 linting',
                                repo: "${GITREPO}",
                                sha: "${ghprbActualCommit}",
                                targetUrl: "${BUILD_URL}",
                                status: 'SUCCESS')
                        }
                        failure {
                            githubNotify (
                                account: 'bbc',
                                credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9',
                                context: "lint/flake8",
                                description: 'Flake8 linting',
                                repo: "${GITREPO}",
                                sha: "${ghprbActualCommit}",
                                targetUrl: "${BUILD_URL}",
                                status: 'FAILURE')
                        }
                    }
                }
                stage ("python2.7 unit tests") {
                    when {
                        environment (
                            name: "TEST_PY27",
                            value: "true")
                    }
                    steps {
                        dir ("py2.7") {
                            githubNotify (
                                account: "${GITHUBUSER}",
                                credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9',
                                context: "tests/py27",
                                description: 'Python2.7 Tests',
                                repo: "${GITREPO}",
                                sha: "${ghprbActualCommit}",
                                targetUrl: "${BUILD_URL}",
                                status: 'PENDING')
                            checkout([$class: 'GitSCM',
                                      branches: [[name: '${sha1}']],
                                      doGenerateSubmoduleConfigurations: false,
                                      extensions: [],
                                      submoduleCfg: [],
                                      userRemoteConfigs: [[credentialsId: '7aa7cd3c-8f60-4e88-bbff-c75516908284',
                                                           refspec: '+refs/pull/*:refs/remotes/origin/pr/*',
                                                           url: 'git@github.com:${GITHUBUSER}/${GITREPO}.git']]])
                            withEnv(['HTTP_PROXY=http://www-cache.rd.bbc.co.uk:8080', 
                                     'HTTPS_PROXY=http://www-cache.rd.bbc.co.uk:8080', 
                                     'no_proxy=mirror.rd.bbc.co.uk,.rd.bbc.co.uk,localhost,127.0.0.1,jenkins.rd.bbc.co.uk', 
                                     'PIP_EXTRA_INDEX_URL=https://artifactory.virt.ch.bbc.co.uk/artifactory/api/pypi/ap-python/simple', 
                                     'PIP_CLIENT_CERT=/etc/pki/tls/private/client_crt_key.pem']) {
                                sh 'tox -e py27'
                            }
                        }
                    }
                    post {
                        success {
                            githubNotify (
                                account: 'bbc',
                                credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9',
                                context: "tests/py27",
                                description: 'Python2.7 Tests',
                                repo: "${GITREPO}",
                                sha: "${ghprbActualCommit}",
                                targetUrl: "${BUILD_URL}",
                                status: 'SUCCESS')
                        }
                        failure {
                            githubNotify (
                                account: 'bbc',
                                credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9',
                                context: "tests/py27",
                                description: 'Python2.7 Tests',
                                repo: "${GITREPO}",
                                sha: "${ghprbActualCommit}",
                                targetUrl: "${BUILD_URL}",
                                status: 'FAILURE')
                        }
                    }
                }
                stage ("python3 unit tests") {
                    when {
                        environment name: "TEST_PY3", value: "true"
                    }
                    steps {
                        dir ("py3") {
                            githubNotify (
                                account: "${GITHUBUSER}",
                                credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9',
                                context: "tests/py3",
                                description: 'Python3 Tests',
                                repo: "${GITREPO}",
                                sha: "${ghprbActualCommit}",
                                targetUrl: "${BUILD_URL}",
                                status: 'PENDING')
                            checkout([$class: 'GitSCM',
                                      branches: [[name: '${sha1}']],
                                      doGenerateSubmoduleConfigurations: false,
                                      extensions: [],
                                      submoduleCfg: [],
                                      userRemoteConfigs: [[credentialsId: '7aa7cd3c-8f60-4e88-bbff-c75516908284',
                                                           refspec: '+refs/pull/*:refs/remotes/origin/pr/*',
                                                           url: 'git@github.com:${GITHUBUSER}/${GITREPO}.git']]])
                            withEnv(['HTTP_PROXY=http://www-cache.rd.bbc.co.uk:8080', 
                                     'HTTPS_PROXY=http://www-cache.rd.bbc.co.uk:8080', 
                                     'no_proxy=mirror.rd.bbc.co.uk,.rd.bbc.co.uk,localhost,127.0.0.1,jenkins.rd.bbc.co.uk', 
                                     'PIP_EXTRA_INDEX_URL=https://artifactory.virt.ch.bbc.co.uk/artifactory/api/pypi/ap-python/simple', 
                                     'PIP_CLIENT_CERT=/etc/pki/tls/private/client_crt_key.pem']) {
                                sh 'tox -e py3'
                            }
                        }
                    }
                    post {
                        success {
                            githubNotify (
                                account: "${GITHUBUSER}",
                                credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9',
                                context: "tests/py3",
                                description: 'Python3 Tests',
                                repo: "${GITREPO}",
                                sha: "${ghprbActualCommit}",
                                targetUrl: "${BUILD_URL}",
                                status: 'SUCCESS')
                        }
                        failure {
                            githubNotify (
                                account: "${GITHUBUSER}",
                                credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9',
                                context: "tests/py3",
                                description: 'Python3 Tests',
                                repo: "${GITREPO}",
                                sha: "${ghprbActualCommit}",
                                targetUrl: "${BUILD_URL}",
                                status: 'FAILURE')
                        }
                    }
                }
                stage ("debian packaging") {
                    when {
                        environment (
                            name: "BUILD_DEB",
                            value: "true")
                    }
                    steps {
                        dir ("deb") {
                            githubNotify (
                                account: "${GITHUBUSER}",
                                credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9',
                                context: "package/deb",
                                description: 'Package Deb',
                                repo: "${GITREPO}",
                                sha: "${ghprbActualCommit}",
                                targetUrl: "${BUILD_URL}",
                                status: 'PENDING')
                            checkout([$class: 'GitSCM',
                                      branches: [[name: '${sha1}']],
                                      doGenerateSubmoduleConfigurations: false,
                                      extensions: [],
                                      submoduleCfg: [],
                                      userRemoteConfigs: [[credentialsId: '7aa7cd3c-8f60-4e88-bbff-c75516908284',
                                                           refspec: '+refs/pull/*:refs/remotes/origin/pr/*',
                                                           url: 'git@github.com:${GITHUBUSER}/${GITREPO}.git']]])
                            sh 'rm -rf deb_dist'
                            sh 'python ./setup.py sdist'
                            sh 'make dsc'
                            dir ('deb_dist') {
                                sh '${WORKSPACE}/scripts/pbuild.sh'
                            }
                        }
                    }
                    post {
                        success {
                            archiveArtifacts 'deb/_result/*'
                            stash (
                                includes: 'deb/_result/*',
                                name: 'deb')
                            githubNotify (
                                account: "${GITHUBUSER}",
                                credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9',
                                context: "package/deb",
                                description: 'Package Deb',
                                repo: "${GITREPO}",
                                sha: "${ghprbActualCommit}",
                                targetUrl: "${BUILD_URL}",
                                status: 'SUCCESS')
                        }
                        failure {
                            githubNotify (
                                account: "${GITHUBUSER}",
                                credentialsId: '543485aa-75b4-49ab-a497-12de62b452f9',
                                context: "package/deb",
                                description: 'Package Deb',
                                repo: "${GITREPO}",
                                sha: "${ghprbActualCommit}",
                                targetUrl: "${BUILD_URL}",
                                status: 'FAILURE')
                        }
                    }
                }
            }
            failFast true
        }
        stage ("upload to artifactory") {
            when {
                allOf {
                    environment name: "sha1", value: "master"
                    environment name: "UPLOAD_TO_ARTIFACTORY", value: "true"
                }
            }
            steps {
                dir ("pydist") {
                    checkout([$class: 'GitSCM',
                              branches: [[name: '${sha1}']],
                              doGenerateSubmoduleConfigurations: false,
                              extensions: [],
                              submoduleCfg: [],
                              userRemoteConfigs: [[credentialsId: '7aa7cd3c-8f60-4e88-bbff-c75516908284',
                                                   refspec: '+refs/pull/*:refs/remotes/origin/pr/*',
                                                   url: 'git@github.com:${GITHUBUSER}/${GITREPO}.git']]])
                    sh 'rm -rf dist/*'
                    withEnv(['HTTP_PROXY=http://www-cache.rd.bbc.co.uk:8080', 
                             'HTTPS_PROXY=http://www-cache.rd.bbc.co.uk:8080', 
                             'no_proxy=mirror.rd.bbc.co.uk,.rd.bbc.co.uk,localhost,127.0.0.1,jenkins.rd.bbc.co.uk', 
                             'PIP_EXTRA_INDEX_URL=https://artifactory.virt.ch.bbc.co.uk/artifactory/api/pypi/ap-python/simple', 
                             'PIP_CLIENT_CERT=/etc/pki/tls/private/client_crt_key.pem']) {
                        sh '${WORKSPACE}/scripts/create_wheel.sh py27'
                        sh '${WORKSPACE}/scripts/create_wheel.sh py3'
                        withCredentials([usernamePassword(credentialsId: '171bbdf4-7ac0-4323-9d5c-a9fdc5317f45',
                                                          passwordVariable: 'ARTIFACTORY_PASSWORD',
                                                          usernameVariable: 'ARTIFACTORY_USERNAME')]) {
                            sh '${WORKSPACE}/scripts/twine_upload.sh py3'
                        }
                    }
                }
            }
        }
        stage ("upload deb") {
            when {
                allOf {
                    environment name: "sha1", value: "master"
                    environment name: "BUILD_DEB", value: "true"
                    environment name: "UPLOAD_DEB", value: "true"
                }
            }
            steps {
                dir("deb") {
                    sh 'rm -rf _result/*'
                    unstash 'deb'
                    sshPublisher(publishers: [sshPublisherDesc(configName: 'Jenkins Master - repomgr',
                                                               transfers: [sshTransfer(excludes: '',
                                                                                       execCommand: '/var/lib/jenkins/repomgr/repo-update ${APT_REPO}/${ENVIRONMENT} ${DEB_DIST} ${ARCH} ${BUILD_TAG} || /var/lib/jenkins/repomgr/repo-update ${APT_REPO}/${ENVIRONMENT} ${DEB_DIST} ${ARCH} FIX',
                                                                                       execTimeout: 300000,
                                                                                       flatten: false,
                                                                                       makeEmptyDirs: false,
                                                                                       noDefaultExcludes: false,
                                                                                       patternSeparator: '[, ]+',
                                                                                       remoteDirectory: '${BUILD_TAG}',
                                                                                       remoteDirectorySDF: false,
                                                                                       removePrefix: '_result/',
                                                                                       sourceFiles: '_result/*')],
                                                               usePromotionTimestamp: false,
                                                               useWorkspaceInPromotion: false,
                                                               verbose: false)])
                }
            }
        }
    }
}
