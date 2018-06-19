@Library("rd-apmm-groovy-ci-library@samn-multiple-ubuntus") _

/*
 Runs the following steps in parallel and reports results to GitHub:
 - Lint using flake8
 - Run Python 2.7 unit tests in tox
 - Run Pythin 3 unit tests in tox
 - Build a Debian package using pbuilder

 If these steps succeed and the master branch is being built, wheels and debs are uploaded to Artifactory and the
 R&D Debian mirrors.

 Optionally you can set FORCE_PYUPLOAD to force upload to Artifactory, and FORCE_DEBUPLOAD to force Debian package
 upload on non-master branches.
*/

pipeline {
    agent {
        label "16.04&&ipstudio-deps"
    }
    parameters {
        booleanParam(name: "FORCE_PYUPLOAD", defaultValue: false, description: "Force Python artifact upload")
        booleanParam(name: "FORCE_DEBUPLOAD", defaultValue: false, description: "Force Debian package upload")
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
                        // Use a workdirectory in /tmp to avoid shebang length limitation
                        sh 'tox -e py27 --recreate --workdir /tmp/$(basename ${WORKSPACE})/tox-py27'
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
                        // Use a workdirectory in /tmp to avoid shebang length limitation
                        sh 'tox -e py3 --recreate --workdir /tmp/$(basename ${WORKSPACE})/tox-py3'
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
                stage ("Debian Source Build") {
                    steps {
                        script {
                            env.deb_result = "FAILURE"
                        }
                        bbcGithubNotify(context: "package/deb", status: "PENDING")

                        sh 'rm -rf deb_dist'
                        sh 'python ./setup.py sdist'
                        sh 'make dsc'
                        bbcPrepareDsc()
                        stash(name: "deb_dist", includes: "deb_dist/*")
                    }
                }
            }
        }
        stage ("Build with pbuilder") {
            steps {
                // Build for all supported platforms and extract results into workspace
                bbcParallelPbuild(stashname: "deb_dist", dists: bbcGetSupportedUbuntuVersions())
            }
            post {
                success {
                    archiveArtifacts artifacts: "_result/**"
                }
                always {
                    // currentResult is governed by the outcome of the pbuilder steps at this point, so we can use it
                    bbcGithubNotify(context: "package/deb", status: currentBuild.currentResult)
                }
            }
        }
        stage ("Upload to Artifactory") {
            when {
                anyOf {
                    expression { return params.FORCE_PYUPLOAD }
                    branch "master"
                }
            }
            steps {
                sh 'rm -rf dist/*'
                bbcMakeWheel("py27")
                bbcMakeWheel("py3")
                bbcTwineUpload(toxenv: "py3")
            }
        }
        stage ("upload deb") {
            when {
                anyOf {
                    expression { return params.FORCE_DEBUPLOAD }
                    branch "master"
                }
            }
            steps {
                script {
                    for (def dist in bbcGetSupportedUbuntuVersions()) {
                        bbcDebUpload(sourceFiles: "_result/${dist}/*", removePrefix: "_result/${dist}", dist: "${dist}",
                                     apt_repo: "ap/python")
                    }
                }
            }
        }
    }
    post {
        always {
            bbcSlackNotify()
        }
    }
}
