@Library(['github.com/indigo-dc/jenkins-pipeline-library@release/2.1.0']) _

def job_result_url = ''

pipeline {
        agent any

    environment {
        author_name = "Fernando Aguilar"
        author_email = "aguilarf@ifca.unican.es"
        app_name = "FAIR_evaluator"
        job_location = "TODO"
        job_location_test = "TODO"
    }

    stages {
        stage('Code_fetching') {
            steps {
                checkout scm
            }
        }
    }

    post {
        failure {
            script {
                currentBuild.result = 'FAILURE'
            }
        }
    }
}
