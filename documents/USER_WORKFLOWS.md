# User Workflows Documentation

This document explains the complete workflow flows for both **Admin (Superuser)** and **Client** users in the nbx-django package management system.

---

## Table of Contents

- [Overview](#overview)
- [Admin (Superuser) Workflow](#admin-superuser-workflow)
- [Client User Workflow](#client-user-workflow)
- [Token Refresh Workflow](#token-refresh-workflow)
- [Permission Matrix](#permission-matrix)
- [Consolidation Status Workflow](#consolidation-status-workflow)

---

## Overview

The nbx-django system follows a role-based access control model:

| Role | Description |
|------|-------------|
| **Admin (Superuser)** | Full system access. Manages clients, packages, consolidations, and tracks the entire logistics workflow. |
| **Client User** | Read-only access to their own data. Can view packages and track shipment status. |

---

## Admin (Superuser) Workflow

As an admin, you manage the entire package lifecycle from client onboarding to final delivery.

### Step 1: Authentication

Obtain a JWT token to access the API:

```graphql
mutation {
  emailAuth(email: "admin@example.com", password: "adminpass") {
    token
    refreshToken
    payload
    refreshExpiresIn
  }
}
```

**Response fields:**
| Field | Description |
|-------|-------------|
| `token` | JWT access token (short-lived) |
| `refreshToken` | Refresh token (long-lived, used to obtain new access tokens) |
| `payload` | Token payload (contains user email, exp, etc.) |
| `refreshExpiresIn` | Refresh token expiration time in seconds |

Include the access token in subsequent requests:
```
Authorization: JWT <your_token>
```

---

### Step 2: Create a Client-User

Create a new client. This automatically creates an associated user account:

```graphql
mutation {
  createClient(
    firstName: "John"
    lastName: "Doe"
    email: "john@example.com"
    identificationNumber: "123456789"
    state: "California"
    city: "Los Angeles"
    mainStreet: "123 Main St"
    mobilePhoneNumber: "+1234567890"
  ) {
    client {
      id
      fullName
      email
      user {
        id
        email
        isActive  # Created as inactive
      }
    }
  }
}
```

**Important Notes:**
- A user account is automatically created with the same email address
- Password is auto-generated (random 16-character token)
- New accounts are created with `isActive: false` (requires activation)

---

### Step 3: Create Packages

Create packages belonging to the client. Capture all logistics details:

```graphql
mutation {
  createPackage(
    barcode: "PKG001"
    courier: "DHL"
    description: "Laptop Computer"
    length: 30.0
    width: 20.0
    height: 5.0
    dimensionUnit: "cm"
    weight: 2.5
    weightUnit: "kg"
    realPrice: 1200.00
    servicePrice: 50.00
    arrivalDate: "2024-01-15"
    clientId: 1  # Client ID from Step 2
  ) {
    package {
      id
      barcode
      client {
        fullName
      }
    }
  }
}
```

---

### Step 4: Create Multiple Packages

Typically, you'll create several packages before consolidating:

```graphql
mutation {
  pkg1: createPackage(
    barcode: "PKG001"
    courier: "DHL"
    description: "Laptop"
    weight: 2.5
    weightUnit: "kg"
    realPrice: 1200.00
    clientId: 1
  ) {
    package { id barcode }
  }
  
  pkg2: createPackage(
    barcode: "PKG002"
    courier: "DHL"
    description: "Mouse"
    weight: 0.5
    weightUnit: "kg"
    realPrice: 25.00
    clientId: 1
  ) {
    package { id barcode }
  }
  
  pkg3: createPackage(
    barcode: "PKG003"
    courier: "FedEx"
    description: "Keyboard"
    weight: 1.0
    weightUnit: "kg"
    realPrice: 80.00
    clientId: 1
  ) {
    package { id barcode }
  }
}
```

---

### Step 5: Create a Consolidation

Group packages into a consolidation with an initial status:

```graphql
mutation {
  createConsolidate(
    description: "John's Tech Order - January 2024"
    status: "pending"  # Options: awaiting_payment, pending, processing
    packageIds: [1, 2, 3]  # Package IDs from previous steps
    deliveryDate: "2024-02-15"
    comment: "Handle with care - contains electronics"
    sendEmail: true  # Notify client via email
  ) {
    consolidate {
      id
      status
      client {
        fullName
        email
      }
      packages {
        barcode
        description
      }
    }
  }
}
```

**Validation Rules:**
- All packages must belong to the same client
- No package can already belong to another consolidation
- Initial status must be: `awaiting_payment`, `pending`, or `processing`

---

### Step 6: Track and Update Status

As the shipment progresses through the pipeline, update the consolidation status:

#### Status Transition Flow:

```
awaiting_payment → pending → processing → in_transit → delivered
        ↓              ↓           ↓            ↓
    cancelled      cancelled   cancelled    cancelled
```

#### Example Status Updates:

**Payment received:**
```graphql
mutation {
  updateConsolidate(
    id: 1
    status: "pending"
    comment: "Payment confirmed"
  ) {
    consolidate {
      id
      status
    }
  }
}
```

**Shipped to destination:**
```graphql
mutation {
  updateConsolidate(
    id: 1
    status: "in_transit"
    comment: "Shipped via FedEx - Tracking: 1234567890"
  ) {
    consolidate {
      id
      status
      comment
    }
  }
}
```

**Final delivery:**
```graphql
mutation {
  updateConsolidate(
    id: 1
    status: "delivered"
    comment: "Delivered and signed by John Doe"
  ) {
    consolidate {
      id
      status
    }
  }
}
```

---

### Step 7: Monitor Dashboard

Admins have access to complete system statistics:

```graphql
query {
  dashboard {
    stats {
      # Package Statistics (All clients)
      totalPackages
      recentPackages
      packagesPending
      packagesInTransit
      packagesDelivered
      
      # Consolidation Statistics
      totalConsolidations
      consolidationsPending
      consolidationsProcessing
      consolidationsInTransit
      consolidationsAwaitingPayment
      
      # Financial Data (Admin only)
      totalRealPrice
      totalServicePrice
      
      # Client Data (Admin only)
      totalClients
    }
    recentPackages(limit: 10) {
      barcode
      description
      realPrice
      client {
        fullName
      }
    }
    recentConsolidations(limit: 5) {
      description
      status
      client {
        fullName
      }
      packages {
        barcode
      }
    }
  }
}
```

---

### Step 8: Query All Clients

Search and browse all clients in the system:

```graphql
query {
  allClients(
    search: "john"
    page: 1
    pageSize: 20
    orderBy: "-createdAt"
  ) {
    results {
      id
      fullName
      email
      mobilePhoneNumber
      city
      state
    }
    totalCount
    page
    hasNext
    hasPrevious
  }
}
```

---

### Admin Summary of Operations

| Category | Operations |
|----------|------------|
| **Client Management** | Create, update, delete any client; view all clients |
| **Package Management** | Create, update, delete packages for any client |
| **Consolidation Management** | Create, update status, delete consolidations |
| **User Management** | Delete user accounts |
| **Financial Data** | View total real price, service price across all packages |
| **System Overview** | Full dashboard access with all statistics |

---

## Client User Workflow

As a client user, you have read-only access to track your own packages and consolidations.

### Step 1: Authentication

Log in with credentials provided by the admin:

```graphql
mutation {
  emailAuth(email: "john@example.com", password: "yourpassword") {
    token
    refreshToken
    payload
    refreshExpiresIn
  }
}
```

**Response fields:**
| Field | Description |
|-------|-------------|
| `token` | JWT access token (short-lived) |
| `refreshToken` | Refresh token (long-lived, used to obtain new access tokens) |
| `payload` | Token payload (contains user email, exp, etc.) |
| `refreshExpiresIn` | Refresh token expiration time in seconds |

---

### Step 2: View Your Profile

```graphql
query {
  me {
    id
    email
    firstName
    lastName
  }
}
```

---

### Step 3: View Your Packages

Access only your own packages:

```graphql
query {
  allPackages(
    page: 1
    pageSize: 20
    orderBy: "-createdAt"
  ) {
    results {
      id
      barcode
      courier
      description
      weight
      weightUnit
      realPrice
      arrivalDate
      createdAt
      consolidate {
        id
        status
      }
    }
    totalCount
    page
    hasNext
    hasPrevious
  }
}
```

---

### Step 4: View Package Details

Get detailed information about a specific package:

```graphql
query {
  package(id: 1) {
    id
    barcode
    courier
    description
    length
    width
    height
    dimensionUnit
    weight
    weightUnit
    realPrice
    servicePrice
    arrivalDate
    comments
    createdAt
    client {
      fullName
      email
    }
    consolidate {
      id
      status
      deliveryDate
      comment
    }
  }
}
```

---

### Step 5: View Your Consolidations

See all your package groupings and their status:

```graphql
query {
  allConsolidates {
    id
    description
    status
    deliveryDate
    comment
    createdAt
    packages {
      id
      barcode
      description
      weight
      weightUnit
    }
  }
}
```

---

### Step 6: View Consolidation Details

Get detailed information about a specific consolidation:

```graphql
query {
  consolidateById(id: 1) {
    id
    description
    status
    deliveryDate
    comment
    extraAttributes
    createdAt
    client {
      fullName
      email
      mobilePhoneNumber
    }
    packages {
      id
      barcode
      description
      weight
      weightUnit
      realPrice
    }
  }
}
```

---

### Step 7: Dashboard (Your Data Only)

View statistics limited to your own data:

```graphql
query {
  dashboard {
    stats {
      totalPackages          # Your packages only
      recentPackages         # Your recent packages
      packagesPending        # Your pending packages
      packagesInTransit      # Your packages in transit
      packagesDelivered      # Your delivered packages
      totalConsolidations    # Your consolidations
      consolidationsPending  # Your pending consolidations
      consolidationsProcessing
      consolidationsInTransit
      consolidationsAwaitingPayment
      totalRealPrice         # Hidden: returns 0
      totalServicePrice      # Hidden: returns 0
      totalClients           # Hidden: returns 0
    }
    recentPackages(limit: 5) {
      barcode
      description
      createdAt
    }
    recentConsolidations(limit: 3) {
      description
      status
      deliveryDate
    }
  }
}
```

---

### Step 8: Update Your Profile (Limited)

Clients can update their own contact information:

```graphql
mutation {
  updateClient(
    id: 1
    mobilePhoneNumber: "+1987654321"
    city: "San Francisco"
  ) {
    client {
      id
      fullName
      mobilePhoneNumber
      city
    }
  }
}
```

**Note:** Email and user association cannot be modified through this mutation.

---

### Client Summary of Operations

| Category | Operations |
|----------|------------|
| **Profile** | View own profile (`me`), update own contact info |
| **Packages** | View own packages only (list and detail) |
| **Consolidations** | View own consolidations only |
| **Dashboard** | View own statistics only (financial data hidden) |
| **Write Operations** | None (read-only system for clients) |

---

## Token Refresh Workflow

Access tokens are short-lived (5 minutes). When your access token expires, use the refresh token to obtain a new one without re-authenticating.

### When to Refresh

- Access tokens expire after 5 minutes
- API requests return authentication errors when the token expires
- Use the **refresh token string** (not the expired access token) to get a new access token
- Refresh tokens are valid for 7 days

### Refresh Token Mutation (Recommended)

Use `refreshWithToken` mutation with your refresh token string:

```graphql
mutation RefreshToken($refreshToken: String!) {
  refreshWithToken(refreshToken: $refreshToken) {
    token
    refreshToken
    payload
    refreshExpiresIn
  }
}
```

**Variables:**
```json
{
  "refreshToken": "62bd6142e47b1f97049bd279b5bc952ae8c4a911"
}
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `refreshToken` | String | Yes | The refresh token string obtained from `emailAuth` |

**Response:**
| Field | Description |
|-------|-------------|
| `token` | New JWT access token (valid for 5 minutes) |
| `refreshToken` | New refresh token (old one is automatically revoked) |
| `payload` | Token payload with user information and updated expiration |
| `refreshExpiresIn` | Refresh token expiration in seconds (7 days) |

**Security Notes:**
- Implements automatic token rotation for enhanced security
- Old refresh token is revoked when new one is issued
- Store both tokens securely on the client
- Never share refresh tokens

### Alternative: Standard JWT Refresh

The library also provides a standard `refreshToken` mutation:

```graphql
mutation {
  refreshToken(token: "<your_jwt_access_token>") {
    token
    payload
  }
}
```

**Note:** This mutation expects the JWT access token, not the refresh token string. Use `refreshWithToken` for the standard refresh token pattern.

### Complete Authentication Flow Example

```graphql
# 1. Initial login
mutation Login {
  emailAuth(email: "user@example.com", password: "password") {
    token        # JWT access token (expires in 5 min) - use for API calls
    refreshToken # Refresh token string (expires in 7 days) - use to get new access token
    payload
    refreshExpiresIn
  }
}

# Response:
# {
#   "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
#   "refreshToken": "62bd6142e47b1f97049bd279b5bc952ae8c4a911",
#   "payload": { "email": "user@example.com", "exp": 1770672036, ... },
#   "refreshExpiresIn": 604800
# }

# 2. Use access token in Authorization header for API calls:
# Authorization: JWT <access_token>

# 3. When access token expires (after 5 minutes), refresh it:
mutation Refresh {
  refreshWithToken(refreshToken: "62bd6142e47b1f97049bd279b5bc952ae8c4a911") {
    token        # New access token
    refreshToken # New refresh token (old one is revoked)
    payload
    refreshExpiresIn
  }
}

# Response:
# {
#   "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",  # New token
#   "refreshToken": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0",  # New refresh token
#   "payload": { "email": "user@example.com", "exp": 1770672336, ... },
#   "refreshExpiresIn": 604800
# }

# 4. Update stored tokens with new values and continue using new access token

# 5. Logout (revokes refresh token)
mutation Logout {
  revokeToken {
    revoked
  }
}
```

### Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Invalid refresh token` | Token not found in database | Login again |
| `Refresh token has expired` | Token older than 7 days | Login again |
| `Refresh token has been revoked` | Token was manually revoked or already used | Login again |

### Client-Side Implementation Tips

**Storage:**
- Store tokens securely (secure storage on mobile, httpOnly cookies on web)
- Never store tokens in localStorage (XSS vulnerability)
- Clear tokens on logout

**Refresh Strategy:**
- Proactively refresh before expiration (e.g., at 4 minutes)
- OR catch 401 errors and refresh on-demand
- Always update both tokens after refresh

**Example JavaScript Implementation:**
```javascript
// Store tokens after login
const loginResponse = await login(email, password);
secureStorage.setItem('accessToken', loginResponse.token);
secureStorage.setItem('refreshToken', loginResponse.refreshToken);

// Refresh function
async function refreshAccessToken() {
  const refreshToken = secureStorage.getItem('refreshToken');
  const response = await fetch('/graphql', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: `
        mutation RefreshToken($refreshToken: String!) {
          refreshWithToken(refreshToken: $refreshToken) {
            token
            refreshToken
            payload
          }
        }
      `,
      variables: { refreshToken }
    })
  });
  
  const { data } = await response.json();
  // Update stored tokens
  secureStorage.setItem('accessToken', data.refreshWithToken.token);
  secureStorage.setItem('refreshToken', data.refreshWithToken.refreshToken);
}

// Automatic retry on 401
async function apiCall(query) {
  const accessToken = secureStorage.getItem('accessToken');
  let response = await fetch('/graphql', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `JWT ${accessToken}`
    },
    body: JSON.stringify({ query })
  });
  
  // If token expired, refresh and retry
  if (response.status === 401) {
    await refreshAccessToken();
    const newToken = secureStorage.getItem('accessToken');
    response = await fetch('/graphql', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `JWT ${newToken}`
      },
      body: JSON.stringify({ query })
    });
  }
  
  return response.json();
}
```

---

## Permission Matrix

### Query Permissions

| Query | Admin | Client | Anonymous |
|-------|-------|--------|-----------|
| `me` | ✅ | ✅ | ❌ |
| `dashboard` | All data | Own data only | ❌ |
| `allClients` | All clients | ❌ | ❌ |
| `client` | Any client | Own only | ❌ |
| `allPackages` | All packages | Own packages only | ❌ |
| `package` | Any package | Own packages only | ❌ |
| `allConsolidates` | All consolidations | ✅ (Note: No restrictions) | ❌ |
| `consolidateById` | Any consolidation | ✅ (Note: No restrictions) | ❌ |

### Mutation Permissions

| Mutation | Admin | Client | Anonymous |
|----------|-------|--------|-----------|
| **Authentication** ||||
| `emailAuth` | ✅ | ✅ | ✅ |
| `refreshWithToken` | ✅ | ✅ | ✅ |
| `refreshToken` | ✅ | ✅ | ✅ |
| `forgotPassword` | ✅ | ✅ | ✅ |
| `resetPassword` | ✅ | ✅ | ✅ |
| `revokeToken` | ✅ | ✅ | ❌ |
| **Client Management** ||||
| `createClient` | ✅ | ❌ | ❌ |
| `updateClient` | Any client | Own only | ❌ |
| `deleteClient` | ✅ | ❌ | ❌ |
| **Package Management** ||||
| `createPackage` | ✅ | ❌ | ❌ |
| `updatePackage` | ✅ | ❌ | ❌ |
| `deletePackage` | ✅ | ❌ | ❌ |
| **Consolidation Management** ||||
| `createConsolidate` | ✅ | ❌ | ❌ |
| `updateConsolidate` | ✅ | ❌ | ❌ |
| `deleteConsolidate` | ✅ | ❌ | ❌ |
| **User Management** ||||
| `deleteUser` | ✅ | ❌ | ❌ |

---

## Consolidation Status Workflow

### Status Values

| Status | Description |
|--------|-------------|
| `awaiting_payment` | Waiting for client payment |
| `pending` | Payment received, awaiting processing |
| `processing` | Being prepared for shipment |
| `in_transit` | Shipped and in transit to destination |
| `delivered` | Successfully delivered |
| `cancelled` | Order cancelled |

### Valid Status Transitions

```
┌──────────────────┐     ┌───────────┐     ┌────────────┐     ┌─────────────┐     ┌───────────┐
│awaiting_payment  │────→│  pending  │────→│ processing │────→│  in_transit │────→│ delivered │
└──────────────────┘     └───────────┘     └────────────┘     └─────────────┘     └───────────┘
        │                      │                  │                   │
        │                      │                  │                   │
        └──────────────────────┴──────────────────┴───────────────────┘
                               ↓
                         ┌───────────┐
                         │ cancelled │
                         └───────────┘
```

| Current Status | Allowed Next Statuses |
|----------------|----------------------|
| `awaiting_payment` | `pending`, `cancelled` |
| `pending` | `processing`, `cancelled` |
| `processing` | `in_transit`, `cancelled` |
| `in_transit` | `delivered`, `cancelled` |
| `delivered` | (none - final state) |
| `cancelled` | (none - final state) |

---

## Complete Example: Admin Creating an Order

```graphql
# 1. Authenticate and get tokens
mutation Login {
  emailAuth(email: "admin@example.com", password: "adminpass") {
    token
    refreshToken
    payload
    refreshExpiresIn
  }
}

# 2. Create client
mutation CreateClient {
  createClient(
    firstName: "Alice"
    lastName: "Smith"
    email: "alice@example.com"
    mobilePhoneNumber: "+1234567890"
  ) {
    client { id fullName email }
  }
}

# 3. Create packages
mutation CreatePackages {
  pkg1: createPackage(
    barcode: "PKG001"
    courier: "DHL"
    description: "Laptop"
    weight: 2.0
    weightUnit: "kg"
    realPrice: 1000.00
    clientId: 1
  ) { package { id barcode } }
  
  pkg2: createPackage(
    barcode: "PKG002"
    courier: "DHL"
    description: "Mouse"
    weight: 0.2
    weightUnit: "kg"
    realPrice: 50.00
    clientId: 1
  ) { package { id barcode } }
}

# 4. Create consolidation
mutation CreateConsolidation {
  createConsolidate(
    description: "Alice's tech order"
    status: "pending"
    packageIds: [1, 2]
    sendEmail: true
  ) {
    consolidate { id status packages { barcode } }
  }
}

# 5. Update status as it progresses
mutation UpdateStatus {
  updateConsolidate(
    id: 1
    status: "in_transit"
    comment: "Shipped today"
  ) {
    consolidate { id status comment }
  }
}

# 6. Refresh token when access token expires
mutation RefreshToken {
  refreshToken(token: "<refresh_token>") {
    token
    payload
  }
}
```

---

## Complete Example: Client Viewing Their Data

```graphql
# 1. Login to get tokens
mutation Login {
  emailAuth(email: "client@example.com", password: "password") {
    token
    refreshToken
    payload
    refreshExpiresIn
  }
}

# 2. Client queries their own data (use access token in header)
query MyData {
  me {
    firstName
    lastName
    email
  }
  
  allPackages {
    results {
      barcode
      description
      realPrice
      consolidate {
        id
        status
        deliveryDate
      }
    }
  }
  
  allConsolidates {
    description
    status
    packages {
      barcode
      description
    }
  }
}
```

---

*Document generated for nbx-django package management system.*
