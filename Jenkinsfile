@Library("rd-apmm-groovy-ci-library@v1.x") _

/*

    This file was autogenerated using tooling in commontooling

    DO NOT MANUALLY EDIT THIS FILE

    Instead make necessary changes to Jenkinsfile.json and then
    regenerate this file with `make static-files` before checking
    the resulting file into git.

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
        booleanParam(name: "FORCE_DOCSUPLOAD", defaultValue: false, description: "Force API docs upload")
        booleanParam(name: "FORCE_PYPIUPLOAD", defaultValue: false, description: "Force upload of python wheels to pypi")
        booleanParam(name: "FORCE_CARETAKER", defaultValue: false, description: "Force run of Artifactory caretaker")
        string(name: "PYTHON_VERSION", defaultValue: "3.10", description: "Python version to make available in tox")
        string(name: "COMMONTOOLING_BRANCH", defaultValue: "main")
    }
    environment {
        FORGE_CERT = "/etc/pki/tls/private/client_crt_key.pem"
        http_proxy = "http://www-cache.rd.bbc.co.uk:8080"
        https_proxy = "http://www-cache.rd.bbc.co.uk:8080"
        PATH = "$HOME/.pyenv/bin:$PATH"
        TOX_WORK_DIR="/tmp/${sh(script: "basename ${WORKSPACE}", , returnStdout: true).trim()}"
        WITH_DOCKER = "true"
        TOX_ENV = "py${(params.PYTHON_VERSION =~ /(\d+)\.(\d+).*/)[0][1..2].join('')}"
        DOCKER_CONFIG = "$WORKSPACE/docker-config/"
    }
    stages {
        stage("Setup Environment") {
            steps {
                bbcStageSetupEnvironment()
            }
            post {
                always {
                    bbcGithubNotify(context: "prepcode", status: env.result)
                }
            }
        }
        stage ("Caretaker: Remove old packages") {
            when {
                anyOf {
                    expression { return params.FORCE_CARETAKER }
                    expression {
                        bbcIsOnBranch(branches: ["main"])
                    }
                }
            }
            steps {
                bbcMake "caretaker"
            }
            post {
                always {
                    bbcGithubNotify(context: "caretaker", status: env.result)
                }
            }
        }
        stage ("make check-static-files") {
            steps {
                bbcMake 'check-static-files'
            }
            post {
                always {
                    bbcGithubNotify(context: "check-static-files", status: env.result)
                }
            }
        }
        stage ("make lint") {
            steps {
                bbcMake 'lint'
            }
            post {
                always {
                    bbcGithubNotify(context: "lint", status: env.result)
                }
            }
        }
        stage ("make mypy") {
            steps {
                bbcMake 'mypy'
            }
            post {
                always {
                    bbcGithubNotify(context: "mypy", status: env.result)
                }
            }
        }
        stage ("make docs") {
            steps {
                bbcMake 'docs'
            }
            post {
                always {
                    bbcGithubNotify(context: "docs", status: env.result)
                }
            }
        }
        stage ("make test") {
            steps {
                bbcMake 'test'
            }
            post {
                always {
                    bbcGithubNotify(context: "test", status: env.result)
                }
            }
        }
        stage ("make wheel") {
            steps {
                bbcMake 'wheel'
            }
            post {
                always {
                    bbcGithubNotify(context: "wheel", status: env.result)
                }
            }
        }
        stage ("Upload to PyPi") {
            when {
                anyOf {
                    expression { return params.FORCE_PYPIUPLOAD }
                    expression { env.TAG_NAME != null }
                    expression {
                        bbcShouldUploadArtifacts(branches: ["main"])
                    }
                }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: "5f2c0fcd-cf71-494a-a642-aa072100171b",
                        passwordVariable: 'TWINE_REPO_PASSWORD',
                        usernameVariable: 'TWINE_REPO_USERNAME')]) {
                    withEnv(["TWINE_REPO=https://upload.pypi.org/legacy/"]) {
                        bbcMake "upload-wheels"
                    }
                }
            }
            post {
                always {
                    bbcGithubNotify(context: "upload-wheels", status: env.result)
                }
            }
        }
        stage ("Upload Docs") {
            when {
                anyOf {
                    expression { return params.FORCE_DOCSUPLOAD }
                    expression { env.TAG_NAME != null }
                    expression {
                        bbcShouldUploadArtifacts(branches: ["main"])
                    }
                }
            }
            steps {
                withBBCStatusRecording(context: 'upload/docs') {
                    bbcAPMMDocsUpload(sourceFiles: "./docs", recursive: true)
                }
            }
            post {
                always {
                    bbcGithubNotify(context: "upload/docs", status: env.result)
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
