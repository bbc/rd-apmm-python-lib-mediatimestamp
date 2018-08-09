@Library("rd-apmm-groovy-ci-library@v1.x") _

/*
 Runs the following steps in parallel and reports results to GitHub:
 - Lint using flake8
 - Run Python 2.7 unit tests in tox
 - Run Pythin 3 unit tests in tox
 - Build Debian packages for supported Ubuntu versions

 If these steps succeed and the master branch is being built, wheels and debs are uploaded to Artifactory and the
 R&D Debian mirrors.

 Optionally you can set FORCE_PYUPLOAD to force upload to Artifactory, and FORCE_DEBUPLOAD to force Debian package
 upload on non-master branches.


 This file makes use of custom steps defined in a BBC internal library for use on our own Jenkins instances. As
 such it will not be immediately useable outside of a BBC environment, but may still serve as inspiration and an
 example of how to implement CI for this package.
*/

pipeline {
    agent {
        label "16.04&&ipstudio-deps"
    }
    options {
        ansiColor('xterm') // Add support for coloured output
        buildDiscarder(logRotator(numToKeepStr: '10')) // Discard old builds
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
                stage ("Unit Tests") {
                    stages {
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
                    }
                }
                stage ("Debian Source Build") {
                    steps {
                        script {
                            env.debSourceBuild_result = "FAILURE"
                        }
                        bbcGithubNotify(context: "deb/sourceBuild", status: "PENDING")

                        sh 'rm -rf deb_dist'
                        sh 'python ./setup.py sdist'
                        sh 'make dsc'
                        bbcPrepareDsc()
                        stash(name: "deb_dist", includes: "deb_dist/*")
                        script {
                            env.debSourceBuild_result = "SUCCESS" // This will only run if the steps above succeeded
                        }
                    }
                    post {
                        always {
                            bbcGithubNotify(context: "deb/sourceBuild", status: env.debSourceBuild_result)
                        }
                    }
                }
            }
        }
        stage ("Build with pbuilder") {
            steps {
                bbcGithubNotify(context: "deb/packageBuild", status: "PENDING")
                // Build for all supported platforms and extract results into workspace
                bbcParallelPbuild(stashname: "deb_dist", dists: bbcGetSupportedUbuntuVersions(), arch: "amd64")
            }
            post {
                success {
                    archiveArtifacts artifacts: "_result/**"
                }
                always {
                    // currentResult is governed by the outcome of the pbuilder steps at this point, so we can use it
                    bbcGithubNotify(context: "deb/packageBuild", status: currentBuild.currentResult)
                }
            }
        }
        stage ("Upload Packages") {
            // Duplicates the when clause of each upload so blue ocean can nicely display when stage skipped
            when {
                anyOf {
                    expression { return params.FORCE_PYUPLOAD }
                    expression { return params.FORCE_DEBUPLOAD }
                    expression {
                        bbcShouldUploadArtifacts(branches: ["master"])
                    }
                }
            }
            parallel {
                stage ("Upload to PyPi") {
                    when {
                        anyOf {
                            expression { return params.FORCE_PYUPLOAD }
                            expression {
                                bbcShouldUploadArtifacts(branches: ["master"])
                            }
                        }
                    }
                    steps {
                        script {
                            env.pypiUpload_result = "FAILURE"
                        }
                        bbcGithubNotify(context: "pypi/upload", status: "PENDING")
                        sh 'rm -rf dist/*'
                        bbcMakeGlobalWheel("py27")
                        bbcMakeGlobalWheel("py3")
                        bbcTwineUpload(toxenv: "py3", pypi: true)
                        script {
                            env.pypiUpload_result = "SUCCESS" // This will only run if the steps above succeeded
                        }
                    }
                    post {
                        always {
                            bbcGithubNotify(context: "pypi/upload", status: env.pypiUpload_result)
                        }
                    }
                }
                stage ("Upload deb") {
                    when {
                        anyOf {
                            expression { return params.FORCE_DEBUPLOAD }
                            expression {
                                bbcShouldUploadArtifacts(branches: ["master"])
                            }
                        }
                    }
                    steps {
                        script {
                            env.debUpload_result = "FAILURE"
                        }
                        bbcGithubNotify(context: "deb/upload", status: "PENDING")
                        script {
                            for (def dist in bbcGetSupportedUbuntuVersions()) {
                                bbcDebUpload(sourceFiles: "_result/${dist}-amd64/*",
                                                removePrefix: "_result/${dist}-amd64",
                                                dist: "${dist}",
                                                apt_repo: "ap/python")
                            }
                        }
                        script {
                            env.debUpload_result = "SUCCESS" // This will only run if the steps above succeeded
                        }
                    }
                    post {
                        always {
                            bbcGithubNotify(context: "deb/upload", status: env.debUpload_result)
                        }
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
