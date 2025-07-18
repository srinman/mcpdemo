# Azure AD App Registration Instructions for Memento MCP Server

This guide provides step-by-step instructions for creating an Azure AD app registration that will be used for OAuth authentication in the Memento MCP Server.

## Prerequisites

- Azure subscription with an Azure AD tenant
- Global Administrator or Application Administrator role in Azure AD
- Access to the Azure Portal

## Step-by-Step Instructions

### Step 1: Navigate to Azure AD

1. Open [Azure Portal](https://portal.azure.com)
2. Sign in with your Azure AD credentials
3. In the left navigation, click on "Azure Active Directory"
4. If you don't see it, use the search bar at the top to find "Azure Active Directory"

### Step 2: Create App Registration

1. In the Azure AD overview page, click on "App registrations" in the left menu
2. Click "New registration" at the top of the page
3. Fill in the registration form:
   - **Name**: `Memento MCP Server`
   - **Supported account types**: Select "Accounts in this organizational directory only (Single tenant)"
   - **Redirect URI**: 
     - Platform: Web
     - URI: `http://localhost:8080/callback`
4. Click "Register" button

### Step 3: Note Important IDs

After registration, you'll see the app overview page. **Copy and save these values**:

- **Application (client) ID**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- **Directory (tenant) ID**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

You'll need these for your `.env` file.

### Step 4: Create Client Secret

1. In the left menu, click on "Certificates & secrets"
2. Click on "New client secret"
3. Fill in the details:
   - **Description**: `Memento MCP Server Secret`
   - **Expires**: Choose "24 months" (or according to your security policy)
4. Click "Add"
5. **IMPORTANT**: Copy the secret **Value** immediately (not the Secret ID)
   - This value will only be shown once!
   - Save it as `AZURE_CLIENT_SECRET` in your `.env` file

### Step 5: Configure API Permissions

1. In the left menu, click on "API permissions"
2. Click "Add a permission"
3. Select "Microsoft Graph"
4. Select "Delegated permissions"
5. Expand "User" and check "User.Read"
6. Click "Add permissions"
7. Click "Grant admin consent for [your tenant name]"
8. Confirm by clicking "Yes"

### Step 6: Update Redirect URI (if needed)

1. In the left menu, click on "Authentication"
2. Under "Redirect URIs", verify that `http://localhost:8080/callback` is listed
3. If not, click "Add URI" and add it
4. Under "Implicit grant and hybrid flows", you can leave all checkboxes unchecked
5. Click "Save" if you made any changes

### Step 7: Configure Your Application

Update your `.env` file with the values you collected:

```bash
# Azure AD Configuration
AZURE_TENANT_ID=your-tenant-id-from-step-3
AZURE_CLIENT_ID=your-client-id-from-step-3
AZURE_CLIENT_SECRET=your-client-secret-from-step-4
```

## Security Considerations

### Production Recommendations

1. **Client Secret Rotation**: Set up a process to rotate client secrets regularly
2. **Conditional Access**: Consider implementing conditional access policies
3. **App Roles**: For more complex scenarios, implement app roles
4. **Certificate Authentication**: Consider using certificates instead of client secrets

### Testing vs Production

- **Testing**: Use the localhost redirect URI as shown above
- **Production**: Update the redirect URI to match your production domain
- **Environment**: Use different app registrations for different environments

## Common Issues and Solutions

### Issue: "AADSTS50011: The reply URL specified in the request does not match the reply URLs configured for the application"

**Solution**: Ensure the redirect URI in your app registration exactly matches `http://localhost:8080/callback`

### Issue: "AADSTS700016: Application with identifier 'xxx' was not found in the directory 'xxx'"

**Solution**: Verify that you're using the correct tenant ID and client ID

### Issue: "AADSTS7000215: Invalid client secret is provided"

**Solution**: Regenerate the client secret and update your `.env` file

### Issue: "AADSTS65001: The user or administrator has not consented to use the application"

**Solution**: Ensure you've granted admin consent for the User.Read permission

## Testing the Configuration

After completing the setup, you can test the configuration:

1. Start the Memento MCP Server: `python memento_server_oauth.py`
2. Start the Memento MCP Client: `python memento_client_oauth.py`
3. The client should automatically open a browser for authentication
4. Sign in with your Azure AD credentials
5. You should see a success message and be redirected back to the application

## Advanced Configuration

### Adding Additional Permissions

If you need additional Microsoft Graph permissions:

1. Go to "API permissions" in your app registration
2. Click "Add a permission"
3. Select "Microsoft Graph"
4. Choose "Delegated permissions"
5. Select the permissions you need (e.g., Files.ReadWrite, Mail.Read)
6. Click "Add permissions"
7. Grant admin consent

### Using App Roles

For more complex authorization scenarios:

1. Go to "App roles" in your app registration
2. Click "Create app role"
3. Define roles like "Admin", "User", etc.
4. Update your application code to check for these roles

### Multi-tenant Configuration

To support users from multiple tenants:

1. Change "Supported account types" to "Accounts in any organizational directory"
2. Update your application to handle multiple tenant IDs
3. Consider implementing tenant-specific configuration

## Monitoring and Maintenance

### Sign-in Logs

Monitor authentication events:
1. Go to Azure AD → "Sign-in logs"
2. Filter by your application name
3. Review successful and failed sign-ins

### App Registration Maintenance

- Regularly review and rotate client secrets
- Monitor permission usage
- Update redirect URIs as needed
- Review sign-in logs for suspicious activity

## Support

If you encounter issues:
1. Check the Azure AD sign-in logs
2. Verify all configuration values
3. Test with a simple OAuth flow first
4. Check Microsoft Graph permissions
5. Ensure your tenant supports the features you're using

For more detailed information, refer to the [Microsoft Identity Platform documentation](https://docs.microsoft.com/en-us/azure/active-directory/develop/).
