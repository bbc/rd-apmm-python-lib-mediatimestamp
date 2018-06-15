@Library("rd-apmm-groovy-ci-library@jamesba-pbuild") _

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
    environment {
        http_proxy = "http://www-cache.rd.bbc.co.uk:8080"
        https_proxy = "http://www-cache.rd.bbc.co.uk:8080"
    }
    stages {
        stage ("parallel jobs") {
            parallel {
                stage ("Linting Check") {
                    steps {
                        script {
                            env.lint_result = "FAILURE"
                        }
                        bbcGithubNotify(context: "lint/flake8", status: "PENDING")
                        sh 'flake8'
                        script {
                            env.lint_result = "SUCCESS" // This will only run if the sh above succeeded
                        }
                    }
                    post {
                        always {
                            bbcGithubNotify(context: "lint/flake8", status: env.lint_result)
                        }
                    }
                }
                stage ("python2.7 unit tests") {
                    steps {
                        script {
                            env.py27_result = "FAILURE"
                        }
                        bbcGithubNotify(context: "tests/py27", status: "PENDING")
                        withBBCRDPythonArtifactory {
                            // Use a workdirectory in /tmp to avoid shebang length limitation
                            sh 'tox -e py27 --workdir /tmp/$(basename ${WORKSPACE})/tox-py27'
                        }
                        script {
                            env.py27_result = "SUCCESS" // This will only run if the sh above succeeded
                        }
                    }
                    post {
                        always {
                            bbcGithubNotify(context: "tests/py27", status: env.py27_result)
                        }
                    }
                }
                stage ("python3 unit tests") {
                    steps {
                        script {
                            env.py3_result = "FAILURE"
                        }
                        bbcGithubNotify(context: "tests/py3", status: "PENDING")
                        withBBCRDPythonArtifactory {
                            // Use a workdirectory in /tmp to avoid shebang length limitation
                            sh 'tox -e py3 --workdir /tmp/$(basename ${WORKSPACE})/tox-py3'
                        }
                        script {
                            env.py3_result = "SUCCESS" // This will only run if the sh above succeeded
                        }
                    }
                    post {
                        always {
                            bbcGithubNotify(context: "tests/py3", status: env.py3_result)
                        }
                    }
                }
                stage ("debian packaging") {
                    steps {
                        script {
                            env.deb_result = "FAILURE"
                        }
                        bbcGithubNotify(context: "package/deb", status: "PENDING")

                        sh 'rm -rf deb_dist'
                        sh 'python ./setup.py sdist'
                        sh 'make dsc'
                        bbcPbuild()
                        script {
                            env.deb_result = "SUCCESS" // This will only run if the commands above succeeded
                        }
                    }
                    post {
                        success {
                            archiveArtifacts '_result/*'
                        }
                        always {
                            bbcGithubNotify(context: "package/deb", status: env.deb_result)
                        }
                    }
                }
            }
        }
        stage ("upload to artifactory") {
            when {
                allOf {
                    not {
                        environment name: "PYUPLOAD", value: "false"
                    }
                    anyOf {
                        environment name: "PYUPLOAD", value: "true"
                        branch 'master'
                    }
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
                    not {
                        environment name: "DEBUPLOAD", value: "false"
                    }
                    anyOf {
                        environment name: "DEBUPLOAD", value: "true"
                        branch 'master'
                    }
                }
            }
            steps {
                bbcDebUpload sourceFiles: '_result/*', removePrefix: '_result/'
            }
        }
    }
}
