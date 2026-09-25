pipeline {
    agent any

    environment {
        IMAGE_NAME = "student-mgmt-app"
        DOCKERHUB_CREDENTIALS = credentials('dockerhub-creds') // configure in Jenkins credentials store
        DOCKERHUB_USER = "your-dockerhub-username"             // <-- change me
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Install & Unit Test') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install -r app/requirements.txt
                    pip install -r tests/requirements-test.txt
                    pytest -q
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} -t ${IMAGE_NAME}:latest ."
            }
        }

        stage('Push to Docker Hub') {
            steps {
                sh '''
                    echo "$DOCKERHUB_CREDENTIALS_PSW" | docker login -u "$DOCKERHUB_CREDENTIALS_USR" --password-stdin
                    docker tag ${IMAGE_NAME}:latest ${DOCKERHUB_USER}/${IMAGE_NAME}:${BUILD_NUMBER}
                    docker tag ${IMAGE_NAME}:latest ${DOCKERHUB_USER}/${IMAGE_NAME}:latest
                    docker push ${DOCKERHUB_USER}/${IMAGE_NAME}:${BUILD_NUMBER}
                    docker push ${DOCKERHUB_USER}/${IMAGE_NAME}:latest
                '''
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    ansible-playbook -i ansible/inventory.ini ansible/deploy.yml \
                        --extra-vars "image=${DOCKERHUB_USER}/${IMAGE_NAME}:latest"
                '''
            }
        }
    }

    post {
        success {
            echo "Pipeline finished: build ${BUILD_NUMBER} deployed."
        }
        failure {
            echo "Pipeline failed - check the stage logs above."
        }
    }
}
