#!/bin/bash
set -e

echo "=========================================================="
echo " Starting DevOps Environment Setup for Sarang Nair (EC2) "
echo "=========================================================="

# 1. Update and install base packages
echo ">>> [1/5] Updating packages and installing Java 17 & Git..."
sudo apt-get update -y
sudo apt-get install -y curl wget apt-transport-https ca-certificates gnupg lsb-release openjdk-17-jre-headless git

# 2. Install Docker
echo ">>> [2/5] Installing Docker Engine..."
sudo apt-get install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ubuntu
sudo chmod 666 /var/run/docker.sock

# 3. Install Jenkins
echo ">>> [3/5] Installing Jenkins..."
sudo wget -O /usr/share/keyrings/jenkins-keyring.asc https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key
echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" | sudo tee /etc/apt/sources.list.d/jenkins.list > /dev/null
sudo apt-get update -y
sudo apt-get install -y jenkins
sudo systemctl enable jenkins
sudo systemctl start jenkins
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins

# 4. Install kubectl
echo ">>> [4/5] Installing kubectl..."
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
rm -f kubectl

# 5. Install Minikube
echo ">>> [5/5] Installing Minikube..."
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
rm -f minikube-linux-amd64

echo ""
echo "=========================================================="
echo "          INSTALLATION COMPLETED SUCCESSFULLY!            "
echo "=========================================================="
echo "Jenkins Status: $(systemctl is-active jenkins)"
echo "Docker Status:  $(systemctl is-active docker)"
echo "Kubectl Version: $(kubectl version --client --short 2>/dev/null || kubectl version --client)"
echo "Minikube Version: $(minikube version --short)"
echo "=========================================================="
echo ""
echo "To view your initial Jenkins Admin Password, run:"
echo "sudo cat /var/lib/jenkins/secrets/initialAdminPassword"
echo ""
