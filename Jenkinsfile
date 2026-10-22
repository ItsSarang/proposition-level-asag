pipeline {
    agent any

    environment {
        DOCKER_USER = 'itssarang'
    }

    stages {
        stage('Clone') {
            steps {
                git branch: 'main', url: 'https://github.com/ItsSarang/proposition-level-asag.git'
            }
        }

        stage('Test') {
            steps {
                sh 'python3 -m py_compile backend/main.py models/registry.py'
            }
        }

        stage('Build Docker Images') {
            steps {
                sh '''
                    docker build -t $DOCKER_USER/asag-backend:latest -f backend/Dockerfile .
                    docker build -t $DOCKER_USER/asag-frontend:latest -f frontend/Dockerfile ./frontend
                '''
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(credentialsId: 'docker-hub-credentials', usernameVariable: 'USER', passwordVariable: 'PASS')]) {
                    sh '''
                        echo "$PASS" | docker login -u "$USER" --password-stdin
                        docker push $DOCKER_USER/asag-backend:latest
                        docker push $DOCKER_USER/asag-frontend:latest
                    '''
                }
            }
        }

        stage('Deploy to Minikube') {
            steps {
                sh '''
                    kubectl apply -f k8s/deployment.yaml
                    kubectl apply -f k8s/service.yaml
                '''
            }
        }

        stage('Verify') {
            steps {
                sh '''
                    kubectl get pods
                    kubectl get svc
                '''
            }
        }
    }
}
