#!/bin/bash
# Build and deploy script for Memento MCP Server to AKS

set -e

# Configuration
REGISTRY_NAME="your-acr-name"  # Replace with your Azure Container Registry name
IMAGE_NAME="memento-mcp-server"
IMAGE_TAG="v1.0.1"
FULL_IMAGE_NAME="${REGISTRY_NAME}.azurecr.io/${IMAGE_NAME}:${IMAGE_TAG}"

echo "🚀 Building and Deploying Memento MCP Server to AKS"
echo "=================================================="

# Step 1: Build Docker image
echo "📦 Building Docker image..."
docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
docker tag ${IMAGE_NAME}:${IMAGE_TAG} ${FULL_IMAGE_NAME}

# Step 2: Push to Azure Container Registry
echo "📤 Pushing to Azure Container Registry..."
# Make sure you're logged in: az acr login --name ${REGISTRY_NAME}
docker push ${FULL_IMAGE_NAME}

# Step 3: Update deployment with new image
echo "🔄 Updating deployment image..."
sed -i "s|image: memento-mcp-server:latest|image: ${FULL_IMAGE_NAME}|g" k8s/deployment.yaml

# Step 4: Apply Kubernetes manifests
echo "🚢 Deploying to AKS..."
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/network-policy.yaml

# Step 5: Wait for deployment
echo "⏳ Waiting for deployment to be ready..."
kubectl rollout status deployment/memento-mcp-server -n memento --timeout=300s

# Step 6: Get service information
echo "📡 Getting service information..."
kubectl get services -n memento

# Step 7: Get external IP
echo "🔍 Waiting for external IP..."
kubectl get service memento-mcp-service -n memento -o jsonpath='{.status.loadBalancer.ingress[0].ip}'

echo ""
echo "✅ Deployment completed successfully!"
echo "🌐 Your Memento MCP Server should be accessible at the external IP on port 8000"
echo "🏥 Health check: http://<EXTERNAL_IP>:8000/health"
echo "📡 MCP endpoint: http://<EXTERNAL_IP>:8000/sse"
echo ""
echo "🔧 Useful commands:"
echo "  kubectl get pods -n memento"
echo "  kubectl logs -f deployment/memento-mcp-server -n memento"
echo "  kubectl get service memento-mcp-service -n memento"
