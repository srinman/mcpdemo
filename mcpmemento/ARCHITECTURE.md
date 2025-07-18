# Memento MCP Demo Architecture Evolution

## Overview

This document outlines the evolution of a Model Context Protocol (MCP) demonstration from a simple local file-based system to a comprehensive Kubernetes deployment example on Azure Kubernetes Service (AKS) with Azure Files storage. The primary use case is to provide users with a natural language interface to store and retrieve personal memories in a centralized, secure location.

## Use Case

The Memento MCP Server demonstrates a simple but practical use case:

- **Purpose**: Enable users to store personal memories, notes, and content using natural language
- **Interface**: Natural language commands like "store this meeting summary" or "find my notes from last week"
- **Storage**: Centralized server with persistent storage and multi-user isolation
- **Access**: Remote access from local workstations to cloud-hosted MCP server

**Important Note**: This example primarily demonstrates remote MCP server deployment on AKS for educational and demonstration purposes. Security considerations (authentication, authorization, encryption) are intentionally simplified and will be addressed in future examples. This is NOT suitable for production use without significant security enhancements.

## Architecture Evolution

### Phase 1: Local File-Based System
**Files**: `memento_server.py`, `memento_client.py`

```
┌─────────────────┐    ┌─────────────────┐
│  Local Client   │────│  Local Server   │
│                 │    │                 │
│ memento_client  │    │ memento_server  │
│     .py         │    │     .py         │
└─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────┐
                       │Local Files  │
                       │Storage      │
                       └─────────────┘
```

**Characteristics**:
- Simple localhost communication
- File-based storage on local machine
- Single user
- No network considerations

### Phase 2: Network-Enabled Local System
**Files**: `servernetwork.py`, `clientnetwork.py`

```
┌─────────────────┐    Network    ┌─────────────────┐
│Network Client   │◄──────────────│Network Server   │
│                 │    (LAN)      │                 │
│ clientnetwork   │               │ servernetwork   │
│     .py         │               │     .py         │
└─────────────────┘               └─────────────────┘
                                         │
                                         ▼
                                  ┌─────────────┐
                                  │Local Files  │
                                  │Storage      │
                                  └─────────────┘
```

**Characteristics**:
- Network communication over LAN
- Server binds to 0.0.0.0 for network access
- Still local file storage
- Introduction of network protocols

### Phase 3: Azure OpenAI Integration
**Files**: `azure_mcp_server.py`, `azure_openai_mcp_client_interactive.py`

```
┌─────────────────┐              ┌─────────────────┐
│Azure OpenAI     │              │  MCP Server     │
│Client           │◄─────────────│                 │
│                 │   Network    │ azure_mcp_      │
│ Interactive     │              │ server.py       │
└─────────────────┘              └─────────────────┘
         │                              │
         ▼                              ▼
┌─────────────────┐              ┌─────────────┐
│Azure OpenAI     │              │Local Files  │
│Service          │              │Storage      │
└─────────────────┘              └─────────────┘
```

**Characteristics**:
- Integration with Azure OpenAI for natural language processing
- MCP protocol implementation
- Interactive client interface
- Cloud AI service integration

### Phase 4: AKS Deployment Example (Current)
**Files**: `memento_mcp_client_interactive.py`, `memento_mcp_server.py`

```
┌─────────────────────────────────────────────────────────────────┐
│                    Local Workstation                            │
│  ┌─────────────────┐                                           │
│  │ MCP Client      │                                           │
│  │ Interactive     │                                           │
│  │                 │◄──────────┐                              │
│  │ memento_mcp_    │           │ HTTPS API                    │
│  │ client_         │           │ (Natural Language            │
│  │ interactive.py  │           │  Processing)                 │
│  └─────────────────┘           │                              │
│           │                    │                              │
│           │ HTTPS/SSE          │                              │
│           │ (YOUR_HOME_IP →    │                              │
│           │  AKS_LOAD_         │                              │
│           │  BALANCER_IP:8000) │                              │
└───────────┼────────────────────┼──────────────────────────────┘
            │                    │
            ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                Azure Cloud Services                             │
│                                                                 │
│  ┌─────────────────┐              ┌─────────────────┐          │
│  │ Azure OpenAI    │              │                 │          │
│  │ Service         │              │ Azure Files     │          │
│  │                 │              │ Persistent      │          │
│  │ - GPT-4o-mini   │              │ Volume          │          │
│  │ - Tool Calling  │              │                 │          │
│  │ - Chat API      │              │ /memento_       │          │
│  └─────────────────┘              │ storage/        │          │
│                                   │ ├── alice/      │          │
│                                   │ ├── bob/        │          │
│                                   │ └── charlie/    │          │
│                                   │                 │          │
│                                   └─────────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                                           ▲
                                           │ Mount
┌─────────────────────────────────────────┼───────────────────────┐
│              Azure Kubernetes Service   │                       │
│                                         │                       │
│  ┌─────────────────┐                    │                      │
│  │ Load Balancer   │                    │                      │
│  │                 │                    │                      │
│  │ Public IP:      │                    │                      │
│  │ AKS_LOAD_       │                    │                      │
│  │ BALANCER_IP     │                    │                      │
│  │                 │                    │                      │
│  │ IP Whitelist:   │                    │                      │
│  │ YOUR_HOME_IP    │                    │                      │
│  └─────────────────┘                    │                      │
│           │                             │                      │
│           │ Session Affinity             │                      │
│           │ (ClientIP)                  │                      │
│           ▼                             │                      │
│  ┌─────────────────┐                    │                      │
│  │                 │                    │                      │
│  │ Pod A           │◄───────────────────┘                      │
│  │ ┌─────────────┐ │ Mount                                     │
│  │ │MCP Server   │ │                                           │
│  │ │             │ │                                           │
│  │ │memento_mcp_ │ │                                           │
│  │ │server.py    │ │                                           │
│  │ │             │ │                                           │
│  │ │0.0.0.0:8000 │ │                                           │
│  │ └─────────────┘ │                                           │
│  └─────────────────┘                                           │
│                                                                │
│  ┌─────────────────┐                    ▲                     │
│  │                 │                    │                     │
│  │ Pod B           │◄───────────────────┘                     │
│  │ ┌─────────────┐ │ Mount                                    │
│  │ │MCP Server   │ │                                          │
│  │ │             │ │                                          │
│  │ │memento_mcp_ │ │                                          │
│  │ │server.py    │ │                                          │
│  │ │             │ │                                          │
│  │ │0.0.0.0:8000 │ │                                          │
│  │ └─────────────┘ │                                          │
│  └─────────────────┘                                          │
└─────────────────────────────────────────────────────────────────┘

Data Flow:
1. User: "Store this meeting summary" → MCP Client
2. MCP Client → Azure OpenAI: Natural language processing + tool calling
3. Azure OpenAI → MCP Client: Tool calls (store_memory, retrieve_memories)
4. MCP Client → AKS MCP Server: Execute tool calls via SSE
5. AKS MCP Server → Azure Files: Persist user data
6. Response flows back: Azure Files → MCP Server → MCP Client → User
```

## Key Architectural Components

### 1. Client Architecture

**Location**: Local workstation (`/home/srinman/git/mcp-hello/mcpmemento/memento_mcp_client_interactive.py`)

**Features**:
- **Environment Configuration**: Reads MCP server hostname from `.env` file
- **Azure OpenAI Integration**: Natural language processing for memory operations
- **SSE Communication**: Server-Sent Events for real-time MCP communication
- **Multi-user Support**: User isolation and session management
- **Interactive Interface**: Menu-driven command interface

**Configuration**:
```bash
# .env file
MCP_SERVER_HOSTNAME=AKS_LOAD_BALANCER_IP  # AKS Load Balancer IP
MCP_SERVER_PORT=8000
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key
```

### 2. Server Architecture

**Location**: AKS Pod (`memento_mcp_server.py`)

**Features**:
- **FastMCP Framework**: Rapid MCP server development
- **User Isolation**: Separate storage directories per user
- **Persistent Storage**: Azure Files mounted volume
- **Network Binding**: Patched to listen on 0.0.0.0:8000
- **Memory Operations**: Store, retrieve, search, delete, statistics

**Key Tools**:
- `store_memory`: Save content with tags and metadata
- `retrieve_memories`: Search with natural language queries
- `get_memory_content`: Retrieve full content
- `list_users`: Multi-tenant user management
- `get_user_stats`: Storage analytics

### 3. Storage Architecture

**Azure Files Configuration**:
```yaml
# Persistent Volume Claim
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: memento-storage-pvc
spec:
  accessModes:
    - ReadWriteMany  # Multiple pods can read/write
  resources:
    requests:
      storage: 10Gi
  storageClassName: azurefile-csi  # Azure Files CSI driver
```

**Directory Structure**:
```
/memento_storage/
├── alice/
│   ├── 20250714_212005_memory.txt
│   ├── 20250714_212005_memory.txt.meta
│   └── ...
├── bob/
│   ├── 20250715_105856_memory.txt
│   ├── 20250715_105856_memory.txt.meta
│   └── ...
└── charlie/
    └── ...
```

### 4. Network Architecture

**Load Balancer Configuration**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: memento-mcp-service
  annotations:
    # IP Whitelisting
    service.beta.kubernetes.io/azure-load-balancer-source-ranges: "YOUR_HOME_IP/32"
spec:
  type: LoadBalancer
  ports:
  - port: 8000
    targetPort: 8000
  # Session Affinity for SSE connections
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 10800  # 3 hours
```

## Session Affinity: Why It's Critical

### The Problem Without Session Affinity

```
# Without Session Affinity - Requests can go to any pod
Request 1: Client → Load Balancer → Pod A (SSE connection established)
Request 2: Client → Load Balancer → Pod B (SSE connection lost!)
Request 3: Client → Load Balancer → Pod C (yet another pod)
```

**Issues**:
- SSE connections break randomly
- MCP session state is lost
- User experience becomes unreliable

### The Solution With Session Affinity

```yaml
sessionAffinity: ClientIP
sessionAffinityConfig:
  clientIP:
    timeoutSeconds: 10800  # 3 hours
```

**Benefits**:
```
# All requests from same IP go to same pod
Request 1: YOUR_HOME_IP → Load Balancer → Pod A
Request 2: YOUR_HOME_IP → Load Balancer → Pod A (same pod!)
Request 3: YOUR_HOME_IP → Load Balancer → Pod A (consistent!)
```

**Why ClientIP Works Here**:
- Single user from whitelisted IP (YOUR_HOME_IP)
- SSE connections require persistent state
- 3-hour timeout balances session stability with failover capability
- Simple and reliable for this use case

### Storage vs Session State

**Storage**: Shared across pods via Azure Files
```bash
Pod A → Azure Files → /memento_storage/alice/
Pod B → Azure Files → /memento_storage/alice/ (same data!)
```

**Session State**: Pod-specific memory objects
```python
# These exist only in pod memory
self.sse_client = sse_client(url)
self.read, self.write = await self.sse_client.__aenter__()
self.mcp_session = ClientSession(self.read, self.write)
```

## Key Technical Learnings

### 1. FastMCP Network Binding Limitation

**Problem**: FastMCP hardcodes localhost binding
```python
# FastMCP internal behavior
def run(self, transport="sse"):
    # Internally calls uvicorn with host="127.0.0.1"
    uvicorn.run(app, host="127.0.0.1", port=8000)
```

**Impact**: Server only accepts localhost connections, making it unreachable from Kubernetes services.

**Solution**: Python Monkey Patching
```python
# Monkey patch uvicorn's Config to force host binding
import uvicorn.config
original_config_init = uvicorn.config.Config.__init__

def patched_config_init(self, app, *args, **kwargs):
    # Always override host and port
    kwargs['host'] = '0.0.0.0'  # Listen on all interfaces
    kwargs['port'] = 8000
    print(f"🔧 Patched uvicorn config: host={kwargs['host']}, port={kwargs['port']}")
    return original_config_init(self, app, *args, **kwargs)

uvicorn.config.Config.__init__ = patched_config_init
```

**Why This Works**:
- Runtime method replacement
- Intercepts uvicorn configuration before server starts
- Forces network interface binding without modifying FastMCP source
- Transparent to application logic

### 2. Container Networking vs kubectl port-forward

**Why port-forward worked without patch**:
```bash
# Direct tunnel - bypasses service layer
kubectl port-forward → Pod(127.0.0.1:8000) ✅
```

**Why LoadBalancer failed without patch**:
```bash
# Service routing - requires network interface binding
LoadBalancer → Service → Pod(127.0.0.1:8000) ❌  # Can't reach localhost
LoadBalancer → Service → Pod(0.0.0.0:8000) ✅   # Can reach all interfaces
```

### 3. Environment-Driven Configuration

**Client Flexibility**:
```python
# Environment-based server discovery
MCP_SERVER_HOSTNAME = os.getenv("MCP_SERVER_HOSTNAME", "127.0.0.1")
MCP_SERVER_PORT = os.getenv("MCP_SERVER_PORT", "8000")
DEFAULT_MCP_SERVER_URL = f"http://{MCP_SERVER_HOSTNAME}:{MCP_SERVER_PORT}/sse"
```

**Deployment Scenarios**:
- Development: `MCP_SERVER_HOSTNAME=127.0.0.1`
- AKS Demo: `MCP_SERVER_HOSTNAME=AKS_LOAD_BALANCER_IP`
- Custom Demo: `MCP_SERVER_HOSTNAME=my-server.example.com`

## Security Considerations (Future Work)

**Current State**: Minimal security for demonstration and educational purposes only

**Production Readiness**: This example is NOT production-ready and requires significant security enhancements before any real-world deployment

**Future Enhancements Required for Production**:
- **Authentication**: User authentication and authorization
- **Encryption**: TLS/SSL for data in transit
- **Network Security**: VPN or private endpoints instead of public IP
- **Data Encryption**: Azure Files encryption at rest
- **Access Controls**: RBAC and fine-grained permissions
- **Audit Logging**: Comprehensive access and operation logging

## Deployment Process (Demo/Development Only)

**Warning**: This deployment is for demonstration and development purposes only. Do not use in production environments.

### 1. Build and Push Container
```bash
az acr build --registry srinmantest --image memento-mcp-server:v1.0.5 .
```

### 2. Deploy to AKS
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### 3. Configure Client
```bash
# .env file
MCP_SERVER_HOSTNAME=AKS_LOAD_BALANCER_IP
```

### 4. Test Connection
```bash
python memento_mcp_client_interactive.py
```

## Conclusion

This architecture demonstrates the evolution from a simple local file system to a comprehensive cloud deployment example. This is a demonstration and educational project showcasing MCP server deployment concepts. The key learning objectives include:

1. **Scalability Concepts**: Kubernetes deployment with multiple replicas
2. **Persistence Patterns**: Azure Files for durable storage
3. **Remote Access Patterns**: Remote access from local workstations
4. **Multi-tenancy Basics**: User isolation in memory storage
5. **AI Integration**: Natural language interface with Azure OpenAI
6. **Network Considerations**: Session affinity for stable connections

The example showcases practical MCP server deployment concepts while highlighting real-world challenges like network binding limitations and the creative solutions (monkey patching) required to overcome them.

**Important**: This foundation provides educational value and demonstrates architectural patterns, but requires significant security and operational enhancements before any production consideration. Future examples will build upon this foundation to address production-ready security, monitoring, and operational concerns.

This demonstrates the viability and potential of remote MCP server architectures in cloud-native environments.
