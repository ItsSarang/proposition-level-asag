# Automatic Short Answer Grading using Semantic and Dependency Analysis

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![CI/CD Pipeline](https://img.shields.io/badge/CI%2FCD-Jenkins%20%2B%20Docker%20%2B%20K8s-blueviolet.svg)](#cloud-computing--devops-cicd-deployment-guide-ccd-cca-2)
[![Tests Passing](https://img.shields.io/badge/tests-694%20passed-brightgreen.svg)](tests/)
[![License: Academic](https://img.shields.io/badge/License-Academic%20Research-lightgrey.svg)](#research-integrity-note)

## Project Overview

This repository houses an undergraduate Natural Language Processing (NLP) / Automated Short Answer Grading (ASAG) research project combined with a production-grade Cloud & DevOps automated CI/CD pipeline. The primary deliverable is an interpretable ASAG research engine designed for systematic experimentation, evaluation, and empirical comparison against human grading.

The project investigates classical semantic and dependency-based ASAG methodology (inspired by Basak et al., 2019) and extends it with a proposition-level analysis layer to assess unmatched student information (correct additional, irrelevant, and incorrect misconceptions).

---

## Research Question

> **"Can an interpretable proposition-level extension of a classical semantic/dependency-based ASAG system evaluate unmatched student information as correct additional, irrelevant, or incorrect information, and does incorporating this evaluation improve agreement with human grading?"**

---

## Three-System Architecture

To rigorously evaluate the research question, three distinct systems are benchmarked:

### 1. Model 1 — Simple Baseline (V0)
A surface-level lexical similarity baseline:
```
Student Answer + Reference Answer ──► TF-IDF Vectorizer ──► Cosine Similarity ──► Baseline Score [0.0, 5.0]
```

### 2. Model 2 — Base ASAG (V1)
A modular, interpretable implementation inspired by the classical methodology of Basak et al. (2019):
```
Question + Reference + Student ──► Linguistic Parse ──► SPO Triples ──► 4-Tier WordNet Matching ──► Directional Entailment ──► Reference Coverage [0.0, 5.0]
```

### 3. Model 3 — Proposed Proposition-Level ASAG (V5)
The complete proposed engine featuring canonical fragment reconstruction, core paraphrase recovery, 4-way unmatched proposition classification, contradiction guards, and calibrated scoring:
```
Question + Reference + Student 
       │
       ▼
Base ASAG Analysis ──► Matched Core Propositions
       │
       ▼
Unmatched Student Propositions ──► Epistemic Domain Verification (4-Way Classification)
       ├── CORRECT_ADDITIONAL (Soft-gated bonus with reference prerequisite)
       ├── IRRELEVANT (Zero score effect, diagnostic transparency)
       ├── INCORRECT (Severity-graded deduction: Minor, Moderate, Core Invalidation)
       └── UNCERTAIN (Zero score effect, epistemic safety reservation)
       │
       ▼
Contradiction Guarding (Negation & Property Antithesis Detection)
       │
       ▼
Model D2 Severity Scoring + Zero-Anchored Calibration ──► Final Calibrated Grade [0.0, 5.0]
```

---

## Benchmark Results ($N = 2,273$ Active Records)

Evaluated on the official **UNT Computer Science Short Answer Dataset (Version 2.0)** (Mohler et al., 2011) across all **81 active questions (2,273 student responses)** against the human average grade (`score_ave`, scale 0.0–5.0):

| Evaluation Metric | Model 1: TF-IDF Baseline | Model 2: Base ASAG (Basak-inspired) | Model 3: Proposed ASAG (Calibrated) | Human Grader Agreement Ceiling\* |
| :--- | :---: | :---: | :---: | :---: |
| **Mean Absolute Error (MAE) ↓** | 2.6571 | 3.8041 | **1.1929** *(55.1% reduction vs M1)* | 0.7263 |
| **Root Mean Squared Error (RMSE) ↓** | 2.9178 | 4.0365 | **1.8242** *(37.5% reduction vs M1)* | 1.2618 |
| **Pearson Correlation ($r$) ↑** | 0.4184 | 0.1383 | **0.4574** ($p < 10^{-117}$) | 0.5910 |
| **Spearman Correlation ($\rho$) ↑** | 0.4424 | 0.1179 | **0.4715** ($p < 10^{-125}$) | 0.5855 |
| **Quadratic Weighted Kappa (QWK) ↑** | 0.1151 | 0.0180 | **0.3557** *($3.1\times$ higher than M1)* | — |
| **Non-Sentential Questions ($r$) ↑** | 0.4681 | 0.0000 *(Total collapse)* | **0.5359** | 0.5892 |

*\*Human agreement ceiling computed on Assignments 1–10 ($N = 1,721$) where two human graders independently scored responses.*

For the complete camera-ready paper draft with all 5 high-resolution figures, see:
- **Research Paper**: [`reports/IEEE_ASAG_Research_Paper.md`](reports/IEEE_ASAG_Research_Paper.md)
- **Publication Figures**: [`reports/figures/`](reports/figures/)

---

## Cloud Computing & DevOps (CI/CD) Deployment Guide (CCD CCA 2)

This repository incorporates an automated CI/CD pipeline meeting the requirements of **TYCSE Cloud Computing and DevOps Continuous Assessment 2 (CCD CCA 2)**.

```
+----------------------------------------------------------------------------------------------------+
|                                    AUTOMATED CI/CD PIPELINE FLOW                                   |
+----------------------------------------------------------------------------------------------------+

  [GitHub Push]
        │
        ▼
  [Jenkins Server on AWS EC2]
        │
        ├─► Stage 1: Source Code Checkout (Pulls latest Git commit)
        ├─► Stage 2: Build and Test (Executes pytest automated validation)
        ├─► Stage 3: Docker Build (Builds backend and frontend container images)
        ├─► Stage 4: Push Image (Publishes tagged images to Docker Hub registry)
        ├─► Stage 5: Minikube Deployment (Applies Kubernetes Deployment & Service manifests)
        └─► Stage 6: Verification (Checks rollout status, running pods, and live endpoint)
```

### 1. Mandatory Submission Deliverables Checklist
- [x] **Project Source Code**: Clean, modular repository building without manual fixes.
- [x] **`Dockerfile`**: Root production Dockerfile + independent [`backend/Dockerfile`](backend/Dockerfile) and [`frontend/Dockerfile`](frontend/Dockerfile).
- [x] **`Jenkinsfile`**: Declarative automated CI/CD pipeline covering all required stages.
- [x] **`k8s/` Manifests**:
  - [`k8s/deployment.yaml`](k8s/deployment.yaml): Deployments for `asag-backend` and `asag-frontend` (2 replicas each, resource limits, health probes).
  - [`k8s/service.yaml`](k8s/service.yaml): Internal `ClusterIP` for backend and `NodePort: 30080` for frontend on Minikube.
- [x] **Container Registry**: Images published to Docker Hub (`sarangnair/asag-backend`, `sarangnair/asag-frontend`).

---

### 2. Pipeline Stages Explained

| Stage | Name | Action Performed |
| :---: | :--- | :--- |
| **1** | **Checkout** | Pulls the latest code commit automatically from GitHub using SCM webhooks. |
| **2** | **Build & Test** | Validates the Python environment and executes unit smoke tests (`pytest tests/common/test_model_registry.py`). |
| **3** | **Docker Build** | Compiles the Python ASAG engine and builds the React Vite static assets into container images. |
| **4** | **Push Image** | Authenticates securely with Docker Hub using Jenkins credentials and pushes tagged versions (`:${BUILD_NUMBER}`) and `:latest`. |
| **5** | **Deploy** | Applies `kubectl apply -f k8s/` to deploy pods and services to the Minikube cluster and updates container image tags. |
| **6** | **Verify** | Runs `kubectl rollout status` and prints running pods, service endpoints, and Minikube access URLs. |

---

### 3. Step-by-Step Setup & Deployment Instructions

#### A. Running Locally with Docker Compose
To launch the full stack (backend API on port `8000` + frontend UI on port `3000`) locally:
```bash
docker compose up --build -d
```
Verify the services:
```bash
curl http://localhost:8000/api/health
# Open http://localhost:3000 in your browser
```

#### B. Deploying to Minikube Kubernetes Cluster
Ensure Minikube and `kubectl` are installed and running:
```bash
minikube start --driver=docker
```
Apply the Kubernetes manifests from the `k8s/` directory:
```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```
Verify the running pods and services:
```bash
kubectl get deployments -l course=ccd-cca2
kubectl get pods -l course=ccd-cca2
kubectl get services -l course=ccd-cca2
```
Access the application in your browser:
```bash
minikube service frontend --url
# Or visit: http://$(minikube ip):30080
```

#### C. Configuring Jenkins on AWS EC2
1. **EC2 Instance Provisioning**:
   - Ubuntu 22.04 LTS (t3.medium or larger recommended).
   - Inbound Security Group ports: `22` (SSH), `8080` (Jenkins Web UI), `8000` (Backend API), `30080` (NodePort).
2. **Install Required Tools on AWS EC2**:
   ```bash
   sudo apt update && sudo apt install -y openjdk-17-jre docker.io git curl
   sudo usermod -aG docker jenkins
   sudo systemctl restart docker jenkins
   ```
3. **Jenkins Configuration**:
   - Install plugins: *Git Plugin*, *Pipeline*, *Docker Pipeline*, *Credentials Binding*.
   - Add Docker Hub credentials in Jenkins: **Manage Jenkins** $\to$ **Credentials** $\to$ ID: `docker-hub-credentials`.
   - Create a **Pipeline Job** pointing to your GitHub repository with script path `Jenkinsfile`.

---

### 4. How to Demonstrate the Code-Change Redeployment (For Viva)

To satisfy the mandatory requirement: *"After the first successful run, you must change the source code, push it, and run the pipeline again to show the new version being deployed"*:

1. Modify a user-facing string or component (for example, edit the greeting or version header in `frontend/src/App.tsx` or `backend/main.py`).
2. Commit and push the change to GitHub:
   ```bash
   git commit -am "chore(viva): bump version display to v5.1.0 for CI/CD demonstration"
   git push origin main
   ```
3. Trigger the Jenkins pipeline (or observe automatic GitHub webhook triggering).
4. Watch Jenkins execute the 6 stages, publish image tag `:${BUILD_NUMBER}`, and execute rolling update in Minikube:
   ```bash
   kubectl rollout status deployment/asag-frontend
   ```
5. Refresh the browser at `http://$(minikube ip):30080` to demonstrate the live updated code running without downtime!

---

## Repository Structure

```text
proposition-level-asag/
├── backend/                        # Flask ASAG REST API Engine
│   ├── api/                        # REST endpoints (/api/grade, /api/analyze)
│   ├── services/                   # Analysis & ModelRegistry integration service
│   ├── Dockerfile                  # Production Backend Dockerfile
│   └── requirements.txt
├── frontend/                       # Interactive React + Vite Workbench
│   ├── src/                        # Proposition visualizer & submission components
│   ├── Dockerfile                  # Multi-stage Vite + Nginx Dockerfile
│   └── nginx.conf                  # Nginx reverse proxy (/api/ -> backend:8000)
├── k8s/                            # [MANDATORY FOR CCA 2] Kubernetes Manifests
│   ├── deployment.yaml             # Deployments for backend & frontend (2 replicas each)
│   └── service.yaml                # ClusterIP (backend) & NodePort:30080 (frontend)
├── models/                         # The 3 Registered ASAG Models
│   ├── registry.py                 # Central discovery registry (V0, V1, V5)
│   ├── v0_tfidf/                   # Model 1 (TF-IDF Baseline)
│   ├── v1_base_asag/               # Model 2 (Base ASAG, Basak et al.)
│   └── v5_proposed/                # Model 3 (Proposed Proposition-Level ASAG)
├── base_asag/                      # Base ASAG clausal dependency pipeline
├── proposed_asag/                  # Proposed ASAG proposition & evidence engine
├── baseline/                       # TF-IDF vectorizer baseline engine
├── common/                         # Shared data structures and interfaces
├── data/                           # Mohler CS ASAG benchmark dataset (v2.0)
├── evaluation/                     # Full benchmark runner scripts and predictions
├── reports/                        # Research paper and generated 300 DPI figures
│   ├── figures/                    # fig1 to fig5 (performance, distributions, ablation)
│   └── IEEE_ASAG_Research_Paper.md # Complete camera-ready research paper
├── notebooks/                      # Clean presentation & analysis notebooks
│   └── ASAG_Engine_Comparison_Presentation.ipynb
├── docs/                           # Documentation and CCA 2 course guides
│   └── devops/
│       └── CCA 2 – Student Guide.pdf
├── tests/                          # 694 unit & integration tests
├── Dockerfile                      # [MANDATORY FOR CCA 2] Root Dockerfile
├── docker-compose.yml              # Local multi-container development
├── Jenkinsfile                     # [MANDATORY FOR CCA 2] Declarative CI/CD Pipeline
├── requirements.txt                # Root Python dependencies
└── README.md                       # Comprehensive Project & DevOps Documentation
```

---

## Research Integrity Note

- **No Fabricated Evidence:** All experimental results, dataset metrics, performance figures, and paper claims are calculated directly from actual pipeline runs across the active Mohler benchmark ($N=2,273$).
- **Deterministic and Interpretable:** The proposition-level engine operates deterministically without opaque neural hallucinations, producing auditable itemized evidence for every graded submission.
