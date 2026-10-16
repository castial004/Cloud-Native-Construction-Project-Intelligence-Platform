# Kubernetes Deployment (minikube)

The platform runs on any Kubernetes cluster. These manifests are tuned for a
local **minikube** cluster (paper Sec. IV-C / VI).

## Prerequisites
- minikube, kubectl, docker

## Deploy

```bash
# 1. Start a cluster and point docker at its daemon (so images are visible).
minikube start
eval "$(minikube docker-env)"

# 2. Build the images inside minikube's daemon.
docker build -t platform-ingestion:latest .
docker build -t platform-pipeline:latest .

# 3. Apply manifests.
kubectl apply -k k8s/

# 4. Wait for Postgres + ingestion, then watch the pipeline job.
kubectl -n ccpip rollout status statefulset/db
kubectl -n ccpip rollout status deployment/ingestion
kubectl -n ccpip wait --for=condition=complete job/ccpip-pipeline --timeout=300s

# 5. Inspect results.
kubectl -n ccpip logs job/ccpip-pipeline
```

## Failover self-healing demonstration (paper Sec. VII)
```bash
# Delete an ingestion pod; Kubernetes recreates it via the Deployment.
kubectl -n ccpip delete pod -l app=ingestion
kubectl -n ccpip get pods -w
```

## Scaling
The ingestion Deployment ships with an HPA (2–6 replicas, 70% CPU target).
```bash
kubectl -n ccpip get hpa
```
