// Declarative Jenkinsfile for Automated CI/CD Pipeline
// Project: Proposition-Level Automated Short Answer Grading (ASAG)
// Course: TYCSE Cloud Computing and DevOps (CCD CCA 2) · Total Marks: 10

pipeline {
    agent any

    environment {
        // Docker Hub repository targets
        DOCKER_USER     = 'sarangnair'
        BACKEND_IMAGE   = 'sarangnair/asag-backend'
        FRONTEND_IMAGE  = 'sarangnair/asag-frontend'
        IMAGE_TAG       = "${env.BUILD_NUMBER ?: 'latest'}"
    }

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
        disableConcurrentBuilds()
    }

    stages {
        stage('1. Source Code Checkout') {
            steps {
                echo "=========================================================="
                echo "STAGE 1: Pulling latest source code from GitHub repository"
                echo "=========================================================="
                checkout scm
                sh 'git log -1 --oneline'
            }
        }

        stage('2. Build and Test') {
            steps {
                echo "=========================================================="
                echo "STAGE 2: Running automated unit tests & smoke validation"
                echo "=========================================================="
                sh '''
                    echo "Checking Python environment..."
                    python3 --version || true
                    if [ -d ".venv" ]; then
                        PYTHONPATH=. .venv/bin/pytest tests/common/test_model_registry.py -v
                    elif command -v pytest >/dev/null 2>&1; then
                        PYTHONPATH=. pytest tests/common/test_model_registry.py -v
                    else
                        echo "Virtualenv not active on agent; running sanity syntax checks..."
                        python3 -m py_compile backend/main.py models/registry.py
                    fi
                '''
            }
        }

        stage('3. Docker Build') {
            steps {
                echo "=========================================================="
                echo "STAGE 3: Building Docker container images (Tag: ${IMAGE_TAG})"
                echo "=========================================================="
                sh '''
                    echo "Building Backend Docker image..."
                    docker build -t ${BACKEND_IMAGE}:${IMAGE_TAG} -t ${BACKEND_IMAGE}:latest -f backend/Dockerfile .

                    echo "Building Frontend Docker image..."
                    docker build -t ${FRONTEND_IMAGE}:${IMAGE_TAG} -t ${FRONTEND_IMAGE}:latest -f frontend/Dockerfile ./frontend

                    echo "Listing generated Docker images..."
                    docker images | grep "asag-"
                '''
            }
        }

        stage('4. Push to Container Registry') {
            steps {
                echo "=========================================================="
                echo "STAGE 4: Publishing images to Docker Hub registry"
                echo "=========================================================="
                // Uses Docker Hub credentials configured in Jenkins Credentials Store
                withCredentials([usernamePassword(credentialsId: 'docker-hub-credentials', usernameVariable: 'DOCKER_USERNAME', passwordVariable: 'DOCKER_PASSWORD')]) {
                    sh '''
                        echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

                        echo "Pushing Backend images..."
                        docker push ${BACKEND_IMAGE}:${IMAGE_TAG}
                        docker push ${BACKEND_IMAGE}:latest

                        echo "Pushing Frontend images..."
                        docker push ${FRONTEND_IMAGE}:${IMAGE_TAG}
                        docker push ${FRONTEND_IMAGE}:latest

                        docker logout
                    '''
                }
            }
        }

        stage('5. Minikube Kubernetes Deployment') {
            steps {
                echo "=========================================================="
                echo "STAGE 5: Deploying manifests to Minikube cluster"
                echo "=========================================================="
                sh '''
                    echo "Applying Kubernetes Deployments and Services..."
                    kubectl apply -f k8s/deployment.yaml
                    kubectl apply -f k8s/service.yaml

                    echo "Updating deployment images to build tag ${IMAGE_TAG}..."
                    kubectl set image deployment/asag-backend asag-backend=${BACKEND_IMAGE}:${IMAGE_TAG} --record || true
                    kubectl set image deployment/asag-frontend asag-frontend=${FRONTEND_IMAGE}:${IMAGE_TAG} --record || true
                '''
            }
        }

        stage('6. Verification & Health Check') {
            steps {
                echo "=========================================================="
                echo "STAGE 6: Verifying rollout status, pods, and accessibility"
                echo "=========================================================="
                sh '''
                    echo "Waiting for Backend rollout..."
                    kubectl rollout status deployment/asag-backend --timeout=120s

                    echo "Waiting for Frontend rollout..."
                    kubectl rollout status deployment/asag-frontend --timeout=90s

                    echo "Active Pods:"
                    kubectl get pods -l course=ccd-cca2 -o wide

                    echo "Active Deployments:"
                    kubectl get deployments -l course=ccd-cca2

                    echo "Active Services:"
                    kubectl get services -l course=ccd-cca2

                    echo "Minikube Service URL Access:"
                    minikube service frontend --url || true
                '''
            }
        }
    }

    post {
        success {
            echo "=========================================================="
            echo "CI/CD PIPELINE SUCCESS: Build #${env.BUILD_NUMBER} deployed successfully!"
            echo "Application is live and ready for evaluation."
            echo "=========================================================="
        }
        failure {
            echo "=========================================================="
            echo "CI/CD PIPELINE FAILED: Build #${env.BUILD_NUMBER} failed."
            echo "Check Jenkins console output for failure diagnostics."
            echo "=========================================================="
        }
        always {
            cleanWs deleteDirs: true, notFailBuild: true
        }
    }
}
