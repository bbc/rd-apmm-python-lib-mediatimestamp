@Library("rd-apmm-groovy-ci-library@master") _

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
                    steps {
                        bbcGithubNotify(context: "lint/flake8", status: "PENDING")
                        sh 'flake8'
                    }
                    post {
                        success {
                            bbcGithubNotify(context: "lint/flake8", status: "SUCCESS")
                        }
                        failure {
                            bbcGithubNotify(context: "lint/flake8", status: "FAILURE")
                        }
                    }
                }
                stage ("python2.7 unit tests") {
                    steps {
                        bbcGithubNotify(context: "tests/py27", status: "PENDING")
                        withBBCRDPythonArtifactory {
                            sh 'tox -e py27'
                        }
                    }
                    post {
                        success {
                            bbcGithubNotify(context: "tests/py27", status: "SUCCESS")
                        }
                        failure {
                            bbcGithubNotify(context: "tests/py27", status: "FAILURE")
                        }
                    }
                }
                stage ("python3 unit tests") {
                    steps {
                        bbcGithubNotify(context: "tests/py3", status: "PENDING")
                        withBBCRDPythonArtifactory {
                            sh 'tox -e py3'
                        }
                    }
                    post {
                        success {
                            bbcGithubNotify(context: "tests/py3", status: "SUCCESS")
                        }
                        failure {
                            bbcGithubNotify(context: "tests/py3", status: "FAILURE")
                        }
                    }
                }
                stage ("debian packaging") {
                    steps {
                        bbcGithubNotify(context: "package/deb", status: "PENDING")

                        sh 'rm -rf deb_dist'
                        sh 'python ./setup.py sdist'
                        sh 'make dsc'
                        dir ('deb_dist') {
                            sh '''
                                cd $(ls|egrep -v "(tar.gz|dsc|orig)"| head -n1)

                                # Update changelog to insert Jenkins build details
                                dch -ljenkins "Jenkins Nightly Build"
                                GITREV=$(git rev-parse --short origin/master)
                                sed -i "s/jenkins1/jenkins${BUILD_NUMBER}~${ENVIRONMENT}~${GITREV}/" debian/changelog

                                # Turn off testing in pybuild
                                sed -i '/%:/i export PYBUILD_DISABLE=test' debian/rules

                                # Rebuild .dsc with changes
                                debuild -uc -us -S
                            '''
                            sh '${WORKSPACE}/scripts/pbuild.sh'
                        }
                    }
                    post {
                        success {
                            archiveArtifacts 'deb/_result/*'
                            stash (
                                includes: 'deb/_result/*',
                                name: 'deb')
                            bbcGithubNotify(context: "package/deb", status: "SUCCESS")
                        }
                        failure {
                            bbcGithubNotify(context: "package/deb", status: "FAILURE")
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
                    withBBCRDPythonArtifactory {
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
