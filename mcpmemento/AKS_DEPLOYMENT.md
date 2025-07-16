# Memento MCP Server - AKS Deployment Guide

This guide will help you deploy the Memento MCP Server to Azure Kubernetes Service (AKS) with a public load balancer and IP whitelisting.

## 🔧 Prerequisites

1. **Azure CLI** installed and configured
2. **kubectl** configured for your AKS cluster
3. **Docker** installed for building the image
4. **Azure Container Registry (ACR)** access

## 🚀 Quick Deployment

### Option 1: Automated Deployment
```bash
# 1. Update the registry name in build-and-deploy.sh
# 2. Run the automated script
./build-and-deploy.sh
```

### Option 2: Manual Deployment

#### Step 1: Build and Push Docker Image
```bash
# Build the Docker image
docker build -t memento-mcp-server:v1.0.0 .

# Tag for your Azure Container Registry
docker tag memento-mcp-server:v1.0.0 your-acr-name.azurecr.io/memento-mcp-server:v1.0.0

# Login to ACR and push
az acr login --name your-acr-name
docker push your-acr-name.azurecr.io/memento-mcp-server:v1.0.0
```

#### Step 2: Update Deployment Manifest
```bash
# Update the image name in k8s/deployment.yaml
sed -i 's|image: memento-mcp-server:latest|image: your-acr-name.azurecr.io/memento-mcp-server:v1.0.0|g' k8s/deployment.yaml
```

#### Step 3: Deploy to AKS
```bash
# Apply all Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/network-policy.yaml

# Wait for deployment to be ready
kubectl rollout status deployment/memento-mcp-server -n memento
```

#### Step 4: Get External IP
```bash
# Get the external IP address
kubectl get service memento-mcp-service -n memento
```

## 🔒 Security Configuration

### IP Whitelisting
The service is configured to only allow traffic from `135.134.199.24/32` (your home network).

To modify the allowed IP ranges:
```yaml
# In k8s/service.yaml
annotations:
  service.beta.kubernetes.io/azure-load-balancer-source-ranges: "135.134.199.24/32,OTHER.IP.ADDRESS/32"
```

### Network Policy
A network policy is configured to restrict pod-to-pod communication within the namespace.

## 📊 Monitoring and Maintenance

### Check Deployment Status
```bash
# View pods
kubectl get pods -n memento

# View services
kubectl get services -n memento

# View logs
kubectl logs -f deployment/memento-mcp-server -n memento
```

### Health Checks
The service includes health check endpoints:
- Health check: `http://<EXTERNAL_IP>:8000/health`
- MCP endpoint: `http://<EXTERNAL_IP>:8000/sse`

### Scaling
```bash
# Scale deployment
kubectl scale deployment memento-mcp-server --replicas=3 -n memento
```

### Updates
```bash
# Update image
kubectl set image deployment/memento-mcp-server memento-mcp-server=your-acr-name.azurecr.io/memento-mcp-server:v1.0.1 -n memento

# Check rollout status
kubectl rollout status deployment/memento-mcp-server -n memento
```

## 🏗️ Architecture Overview

```
Internet (135.134.199.24) 
    ↓
Azure Load Balancer (with IP whitelisting)
    ↓
AKS Cluster
    ↓
Memento MCP Service (LoadBalancer)
    ↓
Memento MCP Pods (2 replicas)
    ↓
Persistent Volume (Azure Files)
```

## 🔧 Configuration

### Environment Variables
- `MCP_SSE_HOST`: Set to `0.0.0.0` for container networking
- `MCP_SSE_PORT`: Set to `8000`
- `PYTHONUNBUFFERED`: Set to `1` for proper logging

### Resources
- **CPU**: 100m requests, 500m limits
- **Memory**: 128Mi requests, 512Mi limits
- **Storage**: 10Gi persistent volume

### Ports
- **Container Port**: 8000
- **Service Port**: 8000
- **External Port**: 8000

## 🚨 Troubleshooting

### Common Issues

1. **External IP Pending**
   ```bash
   # Check AKS configuration
   kubectl describe service memento-mcp-service -n memento
   ```

2. **Pod Not Starting**
   ```bash
   # Check pod logs
   kubectl logs -f pod/<pod-name> -n memento
   ```

3. **Health Check Failing**
   ```bash
   # Test health endpoint
   kubectl port-forward service/memento-mcp-service-internal 8000:8000 -n memento
   curl http://localhost:8000/health
   ```

4. **IP Whitelisting Issues**
   ```bash
   # Update allowed IPs
   kubectl annotate service memento-mcp-service -n memento \
     service.beta.kubernetes.io/azure-load-balancer-source-ranges=135.134.199.24/32,NEW.IP.ADDRESS/32 --overwrite
   ```

## 📝 Next Steps

1. **Test the deployment** by accessing the health endpoint
2. **Configure monitoring** with Azure Monitor or Prometheus
3. **Set up backup** for the persistent volume
4. **Configure SSL/TLS** with Azure Application Gateway if needed
5. **Set up CI/CD pipeline** for automated deployments

## 🔗 Useful Commands

```bash
# View all resources
kubectl get all -n memento

# Delete everything
kubectl delete namespace memento

# View events
kubectl get events -n memento --sort-by=.metadata.creationTimestamp

# Exec into pod
kubectl exec -it deployment/memento-mcp-server -n memento -- /bin/bash
```
