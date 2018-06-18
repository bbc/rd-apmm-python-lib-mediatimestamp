@Library("rd-apmm-groovy-ci-library@jamesba-pbuild") _

/*
 Runs the following steps in parallel and reports results to GitHub:
 - Lint using flake8
 - Run Python 2.7 unit tests in tox
 - Run Pythin 3 unit tests in tox
 - Build a Debian package using pbuilder

 If these steps succeed and the master branch is being built, wheels and debs are uploaded to Artifactory and the
 R&D Debian mirrors.

 Optionally you can set $PYUPLOAD="true" to force upload to Artifactory, and $DEBUPLOAD="true" to force Debian package
 upload on non-master branches.
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
        stage ("Parallel Jobs") {
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
                stage ("Python 2.7 Unit Tests") {
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
                stage ("Python 3 Unit Tests") {
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
                stage ("Debian Packaging") {
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
        stage ("Upload to Artifactory") {
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
                sh 'rm -rf dist/*'
                withBBCRDPythonArtifactory {
                    bbcMakeWheel("py27")
                    bbcMakeWheel("py3")
                    bbcTwineUpload(toxenv: "py3")
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
                bbcDebUpload(sourceFiles: '_result/*', removePrefix: '_result/')
            }
        }
    }
}
