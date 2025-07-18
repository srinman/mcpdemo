# Memento MCP Server with OAuth Authentication

This project demonstrates a Model Context Protocol (MCP) server and client that provides secure, user-specific memory storage using OAuth authentication with Azure AD/Entra ID.

## Features

- **OAuth Authentication**: Secure user authentication using Azure AD/Entra ID
- **User-Specific Data Storage**: Each user's data is stored separately and protected
- **Natural Language Interface**: Use natural language to store and retrieve memories
- **File Storage**: Store files as mementos with metadata
- **Search Capabilities**: Search through stored memories with date and content filters
- **User Switching**: Support for multiple users in the same session
- **Cross-User Protection**: Users cannot access each other's data

## Architecture

- **Server** (`memento_server_oauth.py`): MCP server with OAuth authentication and user-specific data storage
- **Client** (`memento_client_oauth.py`): Interactive client with Azure OpenAI integration and OAuth flow
- **Authentication**: Uses Azure AD/Entra ID for secure user authentication
- **Storage**: File-based storage with user isolation

## Prerequisites

1. **Azure OpenAI Account**: You need an Azure OpenAI resource
2. **Azure AD Tenant**: You need an Azure AD tenant for authentication
3. **Python 3.8+**: Make sure you have Python 3.8 or later installed

## Setup Instructions

### 1. Clone and Install Dependencies

```bash
cd /home/srinman/git/mcp-hello/mcpmementoauth
./setup.sh
```

### 2. Azure AD App Registration

#### Create App Registration:

1. Go to [Azure Portal](https://portal.azure.com) → Azure Active Directory → App registrations
2. Click "New registration"
3. **Name**: "Memento MCP Server"
4. **Supported account types**: "Accounts in this organizational directory only"
5. **Redirect URI**: 
   - Type: Web
   - URI: `http://localhost:8080/callback`
6. Click "Register"

#### Configure App Registration:

1. **Note the IDs**: Copy the "Application (client) ID" and "Directory (tenant) ID"
2. **Create Client Secret**:
   - Go to "Certificates & secrets" → "New client secret"
   - Description: "Memento MCP Server Secret"
   - Expiration: Choose appropriate duration
   - Click "Add" and copy the secret value immediately
3. **Set API Permissions**:
   - Go to "API permissions" → "Add a permission"
   - Select "Microsoft Graph" → "Delegated permissions"
   - Add: `User.Read` (required)
   - Click "Grant admin consent for [your tenant]"

### 3. Configure Environment Variables

Update your `.env` file with the following:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key
AZURE_OPENAI_DEPLOYMENT=gpt-4

# Azure AD Configuration
AZURE_TENANT_ID=your-tenant-id-from-app-registration
AZURE_CLIENT_ID=your-client-id-from-app-registration
AZURE_CLIENT_SECRET=your-client-secret-from-app-registration

# MCP Server Configuration
MCP_SERVER_URL=http://localhost:8000/sse
```

## Usage

### 1. Start the Server

```bash
python memento_server_oauth.py
```

The server will start on `http://localhost:8000/sse`

### 2. Start the Client

```bash
python memento_client_oauth.py
```

### 3. Authentication Flow

1. The client will automatically open your browser
2. Sign in with your Azure AD credentials
3. Grant permissions to the application
4. Return to the client application

### 4. Natural Language Commands

Once authenticated, you can use natural language commands:

```
"Hey memento, store this file with content: Hello World"
"Remember that I like pizza"
"What did I store last week?"
"Store this meeting note: Met with John about project X"
"Retrieve my files from yesterday"
"Store this code snippet: print('Hello World')"
```

## API Reference

### Server Tools

- `authenticate(access_token, session_id)`: Authenticate user with OAuth token
- `store_memento(content, title, tags, session_id)`: Store text memento
- `retrieve_mementos(query, days_back, session_id)`: Retrieve mementos with filters
- `store_file_memento(filename, content, description, session_id)`: Store file as memento
- `retrieve_file_memento(filename, session_id)`: Retrieve file memento
- `list_users(session_id)`: List all users (admin function)

### Client Features

- Interactive chat interface
- Natural language processing via Azure OpenAI
- OAuth authentication flow
- User switching capability
- Conversation history management
- Example conversations for testing

## Security Features

### User Data Isolation
- Each user gets a separate directory based on hashed user ID
- Cross-user data access is prevented
- Session-based authentication ensures user context

### OAuth Security
- Secure token exchange with Azure AD
- Token validation against Microsoft Graph
- Proper session management
- Automatic token refresh (if implemented)

### File Security
- User-specific file storage
- Protected file access
- Metadata tracking for audit trails

## Data Storage Structure

```
user_data/
├── user_a1b2c3d4/          # Hashed user ID directory
│   ├── memento_20240101_120000.json
│   ├── file_notes.txt_20240101_120000.json
│   └── files/
│       └── notes.txt
├── user_e5f6g7h8/          # Another user's directory
│   ├── memento_20240101_130000.json
│   └── files/
│       └── document.pdf
```

## Troubleshooting

### Common Issues

1. **Authentication Failed**: Check Azure AD app registration configuration
2. **Token Verification Failed**: Ensure proper API permissions are granted
3. **MCP Connection Failed**: Make sure the server is running on the correct port
4. **File Access Denied**: Check file permissions and user data directory

### Debug Mode

Set environment variable for debug logging:
```bash
export DEBUG=1
python memento_server_oauth.py
```

## Development

### Adding New Tools

1. Add tool function to `memento_server_oauth.py`
2. Update tool definitions in `memento_client_oauth.py`
3. Test with the interactive client

### Extending Authentication

The current implementation uses a simplified OAuth flow. For production:
- Implement proper JWT validation
- Add token refresh capability
- Implement session management
- Add role-based access control

## License

This project is for demonstration purposes and should be adapted for production use with proper security measures.

## Support

For issues and questions, please check:
1. Azure AD app registration configuration
2. Environment variable setup
3. Network connectivity
4. Python dependencies

Remember to keep your client secrets secure and never commit them to version control!
