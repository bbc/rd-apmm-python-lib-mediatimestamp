@Library("rd-apmm-groovy-ci-library@v1.x") _

/*
 Runs the following steps in parallel and reports results to GitHub:
 - Lint using flake8
 - Run Python 2.7 unit tests in tox
 - Run Pythin 3 unit tests in tox
 - Build Debian packages for supported Ubuntu versions

 If these steps succeed and the main branch is being built, wheels and debs are uploaded to Artifactory and the
 R&D Debian mirrors.

 Optionally you can set FORCE_PYUPLOAD to force upload to Artifactory, and FORCE_DEBUPLOAD to force Debian package
 upload on non-main branches.


 This file makes use of custom steps defined in a BBC internal library for use on our own Jenkins instances. As
 such it will not be immediately useable outside of a BBC environment, but may still serve as inspiration and an
 example of how to implement CI for this package.
*/

pipeline {
    agent {
        label "ubuntu&&apmm-agent"
    }
    options {
        ansiColor('xterm') // Add support for coloured output
        buildDiscarder(logRotator(numToKeepStr: '10')) // Discard old builds
    }
    triggers {
        cron(env.BRANCH_NAME == 'main' ? 'H H(0-8) * * *' : '') // Build main some time every morning
    }
    parameters {
        booleanParam(name: "FORCE_PYUPLOAD", defaultValue: false, description: "Force Python artifact upload")
        booleanParam(name: "FORCE_DEBUPLOAD", defaultValue: false, description: "Force Debian package upload")
        booleanParam(name: "FORCE_DOCSUPLOAD", defaultValue: false, description: "Force docs upload")
    }
    environment {
        http_proxy = "http://www-cache.rd.bbc.co.uk:8080"
        https_proxy = "http://www-cache.rd.bbc.co.uk:8080"
        PATH = "$HOME/.pyenv/bin:$PATH"
    }
    stages {
        stage ("Clean") {
            steps {
                sh 'git clean -dfx'
                sh 'make clean'
            }
        }
        stage("Ensure pyenv has python3.10.0") {
            steps {
                bbcSetPythonVersions(versions: "3.10.0")
            }
        }
        stage ("Linting Check") {
            steps {
                script {
                    env.lint_result = "FAILURE"
                }
                bbcGithubNotify(context: "lint/flake8", status: "PENDING")
                sh 'make lint'
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
        stage ("Type Check") {
            steps {
                script {
                    env.mypy_result = "FAILURE"
                }
                bbcGithubNotify(context: "type/mypy", status: "PENDING")
                sh 'make mypy'
                script {
                    env.mypy_result = "SUCCESS" // This will only run if the sh above succeeded
                }
            }
            post {
                always {
                    bbcGithubNotify(context: "type/mypy", status: env.mypy_result)
                }
            }
        }
        stage ("Build Docs") {
            steps {
                sh 'make docs'
            }
        }
        stage ("Python 3 Unit Tests") {
            steps {
                script {
                    env.py3_result = "FAILURE"
                }
                bbcGithubNotify(context: "tests/py3", status: "PENDING")
                // Use a workdirectory in /tmp to avoid shebang length limitation
                sh 'make test'
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
        stage ("Build with pbuilder") {
            steps {
                bbcGithubNotify(context: "deb/packageBuild", status: "PENDING")
                // Build for all supported platforms and extract results into workspace
                bbcParallelPbuild(stashname: "deb_dist",
                                    dists: bbcGetSupportedUbuntuVersions(exclude: ["xenial"]),
                                    arch: "amd64")
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
                    expression { return params.FORCE_DOCSUPLOAD }
                    expression {
                        bbcShouldUploadArtifacts(branches: ["main", "dev"])
                    }
                }
            }
            stages {
                stage ("Upload Docs") {
                    when {
                            anyOf {
                            expression { return params.FORCE_DOCSUPLOAD }
                            expression {
                                bbcShouldUploadArtifacts(branches: ["main"])
                            }
                        }
                    }
                    steps {
                        bbcAPMMDocsUpload(sourceFiles: "./docs/*.html")
                    }
                }
                stage ("Upload to PyPi") {
                    when {
                        anyOf {
                            expression { return params.FORCE_PYUPLOAD }
                            expression {
                                bbcShouldUploadArtifacts(branches: ["main"])
                            }
                        }
                    }
                    steps {
                        script {
                            env.pypiUpload_result = "FAILURE"
                        }
                        bbcGithubNotify(context: "pypi/upload", status: "PENDING")
                        sh 'rm -rf dist/*'
                        bbcMakeGlobalWheel("py310")
                        bbcTwineUpload(toxenv: "py310", pypi: true)
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
                stage ("Upload to Artifactory") {
                    when {
                        anyOf {
                            expression { return params.FORCE_PYUPLOAD }
                            expression {
                                bbcShouldUploadArtifacts(branches: ["dev"])
                            }
                        }
                    }
                    steps {
                        script {
                            env.artifactoryUpload_result = "FAILURE"
                        }
                        bbcGithubNotify(context: "artifactory/upload", status: "PENDING")
                        sh 'rm -rf dist/*'
                        bbcMakeGlobalWheel("py310")
                        bbcTwineUpload(toxenv: "py310", pypi: false)
                        script {
                            env.artifactoryUpload_result = "SUCCESS" // This will only run if the steps above succeeded
                        }
                    }
                    post {
                        always {
                            bbcGithubNotify(context: "artifactory/upload", status: env.artifactoryUpload_result)
                        }
                    }
                }
                stage ("Upload deb") {
                    when {
                        anyOf {
                            expression { return params.FORCE_DEBUPLOAD }
                            expression {
                                bbcShouldUploadArtifacts(branches: ["main"])
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
            post {
                always {
                    bbcSlackNotify(channel: "#apmm-cloudfit")
                }
            }
        }
    }
}
