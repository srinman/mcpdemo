#!/bin/bash
# Test Docker build locally

set -e

echo "🐳 Testing Docker build locally"
echo "=============================="

# Step 1: Build the image
echo "📦 Building Docker image..."
docker build -t memento-mcp-server:test .

# Step 2: Run the container
echo "🚀 Starting container..."
docker run -d --name memento-test -p 8000:8000 memento-mcp-server:test

# Step 3: Wait for container to start
echo "⏳ Waiting for container to start..."
sleep 10

# Step 4: Test health endpoint
echo "🏥 Testing health endpoint..."
if curl -f http://localhost:8000/health; then
    echo "✅ Health check passed!"
else
    echo "❌ Health check failed!"
fi

# Step 5: Show logs
echo "📋 Container logs:"
docker logs memento-test

# Step 6: Cleanup
echo "🧹 Cleaning up..."
docker stop memento-test
docker rm memento-test

echo ""
echo "✅ Local Docker test completed!"
echo "🚀 Ready for AKS deployment!"
