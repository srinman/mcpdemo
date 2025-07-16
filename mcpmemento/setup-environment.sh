#!/bin/bash
# Environment setup script for AKS deployment

set -e

# Configuration
RESOURCE_GROUP="your-resource-group"
AKS_CLUSTER="your-aks-cluster"
ACR_NAME="your-acr-name"
LOCATION="eastus"

echo "🔧 Setting up environment for Memento MCP Server deployment"
echo "=========================================================="

# Step 1: Login to Azure
echo "🔑 Logging into Azure..."
az login

# Step 2: Set subscription (if needed)
# az account set --subscription "your-subscription-id"

# Step 3: Connect to AKS cluster
echo "🔌 Connecting to AKS cluster..."
az aks get-credentials --resource-group ${RESOURCE_GROUP} --name ${AKS_CLUSTER}

# Step 4: Verify connection
echo "✅ Verifying AKS connection..."
kubectl cluster-info

# Step 5: Login to ACR
echo "🐳 Logging into Azure Container Registry..."
az acr login --name ${ACR_NAME}

# Step 6: Create namespace if it doesn't exist
echo "📁 Creating namespace..."
kubectl apply -f k8s/namespace.yaml

# Step 7: Check if storage class exists
echo "💾 Checking storage class..."
kubectl get storageclass

echo ""
echo "✅ Environment setup completed!"
echo "🚀 You can now run: ./build-and-deploy.sh"
echo ""
echo "🔧 Current configuration:"
echo "  Resource Group: ${RESOURCE_GROUP}"
echo "  AKS Cluster: ${AKS_CLUSTER}"
echo "  ACR Name: ${ACR_NAME}"
echo "  Location: ${LOCATION}"
