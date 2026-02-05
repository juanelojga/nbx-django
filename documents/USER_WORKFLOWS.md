# User Workflows Documentation

This document explains the complete workflow flows for both **Admin (Superuser)** and **Client** users in the nbx-django package management system.

---

## Table of Contents

- [Overview](#overview)
- [Admin (Superuser) Workflow](#admin-superuser-workflow)
- [Client User Workflow](#client-user-workflow)
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
    payload
    refreshExpiresIn
  }
}
```

Include the token in subsequent requests:
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
    payload
  }
}
```

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
# 1. Create client
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

# 2. Create packages
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

# 3. Create consolidation
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

# 4. Update status as it progresses
mutation UpdateStatus {
  updateConsolidate(
    id: 1
    status: "in_transit"
    comment: "Shipped today"
  ) {
    consolidate { id status comment }
  }
}
```

---

## Complete Example: Client Viewing Their Data

```graphql
# Client queries their own data
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
