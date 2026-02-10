# GraphQL API Documentation

This document provides comprehensive documentation for the nbx-django GraphQL API.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Types](#types)
- [Queries](#queries)
- [Dashboard](#dashboard)
- [Mutations](#mutations)
- [Error Handling](#error-handling)
- [User Permissions](#user-permissions)

## Overview

The GraphQL endpoint is available at `/graphql` (when `DEBUG=True`, GraphiQL interface is enabled).

**Schema Location**: `packagehandling/graphql_schema.py`

### Main Components

| Component | Description |
|-----------|-------------|
| **Types** | `packagehandling/schema/types.py` |
| **Queries** | `packagehandling/schema/queries.py` |
| **Mutations** | `packagehandling/schema/mutations.py` |
| **Query Parts** | `packagehandling/schema/query_parts/` |
| **Mutation Parts** | `packagehandling/schema/mutation_parts/` |

---

## Authentication

The API uses JWT (JSON Web Token) authentication.

### Getting a Token

Use the `emailAuth` mutation to obtain access and refresh tokens:

```graphql
mutation {
  emailAuth(email: "user@example.com", password: "password") {
    token
    refreshToken
    payload
    refreshExpiresIn
  }
}
```

### Using the Token

Include the token in the Authorization header:

```
Authorization: JWT <your_token>
```

### Token Refresh

The API supports two methods for refreshing JWT access tokens:

#### Method 1: Using `refreshWithToken` (Recommended)

Use the `refreshWithToken` mutation with your refresh token string to obtain a new access token and a new refresh token (token rotation):

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
  "refreshToken": "your-refresh-token-string-here"
}
```

**Response:**
- `token`: New JWT access token (valid for 5 minutes)
- `refreshToken`: New refresh token (old one is automatically revoked)
- `payload`: JWT payload with user information
- `refreshExpiresIn`: Refresh token expiration time in seconds (7 days)

**Benefits:**
- Implements token rotation for enhanced security
- Intuitive API matching standard refresh token patterns
- Easy to test in GraphiQL

#### Method 2: Using `refreshToken` (Library Default)

This is the default django-graphql-jwt mutation that expects different parameters:

```graphql
mutation {
  refreshToken(token: "<your_jwt_access_token>") {
    token
    payload
  }
}
```

**Note:** This mutation expects the JWT access token, not the refresh token string.

### Token Verification

```graphql
mutation {
  verifyToken(token: "<your_token>") {
    payload
  }
}
```

### Token Revocation

Revoke a refresh token (requires authentication):

```graphql
mutation {
  revokeToken {
    revoked
  }
}
```

**Note:** This mutation expects the refresh token in an HTTP-only cookie.

---

## Types

### UserType

Represents a user in the system.

| Field | Type | Description |
|-------|------|-------------|
| `id` | ID | User ID |
| `email` | String | User email (unique) |
| `username` | String | Optional username |
| `isSuperuser` | Boolean | Superuser status |
| `isStaff` | Boolean | Staff status |
| `isActive` | Boolean | Account active status |
| `dateJoined` | DateTime | Account creation date |

### MeType

Represents the currently authenticated user with client info.

| Field | Type | Description |
|-------|------|-------------|
| `id` | ID | User ID |
| `email` | String | User email |
| `isSuperuser` | Boolean | Superuser status |
| `firstName` | String | Client's first name (if linked) |
| `lastName` | String | Client's last name (if linked) |

### ClientType

Represents a client/customer.

| Field | Type | Description |
|-------|------|-------------|
| `id` | ID | Client ID |
| `firstName` | String | First name |
| `lastName` | String | Last name |
| `fullName` | String | Computed full name (first + last) |
| `email` | String | Email address |
| `identificationNumber` | String | ID/Document number |
| `state` | String | State/Province |
| `city` | String | City |
| `mainStreet` | String | Main street address |
| `secondaryStreet` | String | Secondary street address |
| `buildingNumber` | String | Building number |
| `mobilePhoneNumber` | String | Mobile phone |
| `phoneNumber` | String | Landline phone |
| `createdAt` | DateTime | Creation timestamp |
| `updatedAt` | DateTime | Last update timestamp |
| `user` | UserType | Associated user account |

### PackageType

Represents a package/shipment.

| Field | Type | Description |
|-------|------|-------------|
| `id` | ID | Package ID |
| `barcode` | String | Unique barcode (unique, immutable) |
| `courier` | String | Courier service name |
| `otherCourier` | String | Alternative courier name |
| `length` | Float | Package length |
| `width` | Float | Package width |
| `height` | Float | Package height |
| `dimensionUnit` | String | Unit for dimensions (e.g., "cm", "in") |
| `weight` | Float | Package weight |
| `weightUnit` | String | Unit for weight (e.g., "kg", "lb") |
| `description` | String | Package description |
| `purchaseLink` | String | URL to purchase receipt |
| `realPrice` | Float | Actual price paid |
| `servicePrice` | Float | Service/shipping price |
| `arrivalDate` | Date | Expected/actual arrival date |
| `comments` | String | Additional comments |
| `client` | ClientType | Package owner |
| `consolidate` | ConsolidateType | Associated consolidation (if any) |
| `createdAt` | DateTime | Creation timestamp |
| `updatedAt` | DateTime | Last update timestamp |

### ConsolidateType

Represents a consolidation of packages.

| Field | Type | Description |
|-------|------|-------------|
| `id` | ID | Consolidation ID |
| `description` | String | Consolidation description |
| `status` | String | Current status (see status values below) |
| `deliveryDate` | Date | Expected delivery date |
| `comment` | String | Additional comments |
| `extraAttributes` | JSON | Flexible additional data |
| `client` | ClientType | Consolidation owner |
| `packages` | [PackageType] | List of consolidated packages |
| `createdAt` | DateTime | Creation timestamp |
| `updatedAt` | DateTime | Last update timestamp |

### DashboardStatsType

Represents dashboard statistics.

| Field | Type | Description |
|-------|------|-------------|
| `totalPackages` | Int | Total number of packages |
| `recentPackages` | Int | Packages created in last 30 days |
| `packagesPending` | Int | Packages without consolidation or pending |
| `packagesInTransit` | Int | Packages in transit |
| `packagesDelivered` | Int | Packages delivered |
| `totalConsolidations` | Int | Total number of consolidations |
| `consolidationsPending` | Int | Consolidations with pending status |
| `consolidationsProcessing` | Int | Consolidations being processed |
| `consolidationsInTransit` | Int | Consolidations in transit |
| `consolidationsAwaitingPayment` | Int | Consolidations awaiting payment |
| `totalRealPrice` | Float | Total real price of all packages (admin only) |
| `totalServicePrice` | Float | Total service price of all packages (admin only) |
| `totalClients` | Int | Total number of clients (admin only) |

### DashboardType

Represents the main dashboard data.

| Field | Type | Description |
|-------|------|-------------|
| `stats` | DashboardStatsType | Dashboard statistics |
| `recentPackages` | [PackageType] | Recent packages (configurable limit) |
| `recentConsolidations` | [ConsolidateType] | Recent consolidations (configurable limit) |

**Consolidate Status Values:**

| Status | Description |
|--------|-------------|
| `awaiting_payment` | Waiting for payment |
| `pending` | Pending processing |
| `processing` | Being processed |
| `in_transit` | In transit to destination |
| `delivered` | Successfully delivered |
| `cancelled` | Cancelled |

**Status Transitions:**
```
awaiting_payment → pending, cancelled
pending → processing, cancelled
processing → in_transit, cancelled
in_transit → delivered, cancelled
delivered → (no transitions)
cancelled → (no transitions)
```

### Connection Types

Used for paginated results:

#### ClientConnection

| Field | Type | Description |
|-------|------|-------------|
| `results` | [ClientType] | List of clients |
| `totalCount` | Int | Total number of results |
| `page` | Int | Current page number |
| `pageSize` | Int | Items per page |
| `hasNext` | Boolean | Has next page |
| `hasPrevious` | Boolean | Has previous page |

#### PackageConnection

Same structure as ClientConnection but with `results: [PackageType]`.

---

## Queries

### User Queries

#### `me`

Returns the currently authenticated user's information.

**Access**: Any authenticated user

```graphql
query {
  me {
    id
    email
    isSuperuser
    firstName
    lastName
  }
}
```

**Returns**: `MeType` or `null` if not authenticated

---

### Client Queries

#### `allClients`

Returns a paginated list of all clients (Superuser only).

**Access**: Superuser only

**Arguments:**

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `search` | String | No | - | Search by name, email, ID, or phone |
| `page` | Int | No | 1 | Page number |
| `pageSize` | Int | No | 10 | Items per page (10, 20, 50, 100) |
| `orderBy` | String | No | - | Sort field: `fullName`, `email`, `createdAt` (prefix with `-` for desc) |

```graphql
query {
  allClients(search: "john", page: 1, pageSize: 20, orderBy: "-createdAt") {
    results {
      id
      fullName
      email
      mobilePhoneNumber
    }
    totalCount
    page
    pageSize
    hasNext
    hasPrevious
  }
}
```

**Returns**: `ClientConnection`

**Errors:**
- `PermissionDenied`: If user is not superuser
- `ValueError`: If invalid `pageSize` or `orderBy` value

---

#### `client`

Returns a single client by ID.

**Access**: Superuser (any client) or own client record

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | Int | Yes | Client ID |

```graphql
query {
  client(id: 1) {
    id
    firstName
    lastName
    email
    state
    city
    mainStreet
    mobilePhoneNumber
  }
}
```

**Returns**: `ClientType`

**Errors:**
- `PermissionDenied`: If regular user requests another client's data
- `Client.DoesNotExist`: If client not found

---

### Package Queries

#### `allPackages`

Returns a paginated list of packages.

**Access**: Superuser (all packages) or own packages only

**Arguments:**

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `search` | String | No | - | Search by barcode or description |
| `page` | Int | No | 1 | Page number |
| `pageSize` | Int | No | 10 | Items per page (10, 20, 50, 100) |
| `orderBy` | String | No | - | Sort field: `barcode`, `createdAt`, `status` |
| `clientId` | Int | No | - | Filter by client ID (superuser only) |
| `notInConsolidate` | Boolean | No | true | Exclude packages already in a consolidation |

```graphql
query {
  allPackages(
    search: "PKG123"
    page: 1
    pageSize: 20
    orderBy: "-createdAt"
    notInConsolidate: true
  ) {
    results {
      id
      barcode
      courier
      description
      realPrice
      servicePrice
      client {
        fullName
      }
    }
    totalCount
    hasNext
  }
}
```

**Returns**: `PackageConnection`

**Errors:**
- `PermissionDenied`: If regular user without client profile
- `ValueError`: If invalid `pageSize` or `orderBy` value

---

#### `package`

Returns a single package by ID.

**Access**: Superuser (any package) or own packages only

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | Int | Yes | Package ID |

```graphql
query {
  package(id: 1) {
    id
    barcode
    courier
    length
    width
    height
    dimensionUnit
    weight
    weightUnit
    realPrice
    servicePrice
    arrivalDate
    client {
      fullName
      email
    }
    consolidate {
      id
      status
    }
  }
}
```

**Returns**: `PackageType`

**Errors:**
- `PermissionDenied`: If package doesn't belong to user
- `Package.DoesNotExist`: If package not found

---

### Consolidate Queries

#### `allConsolidates`

Returns a paginated list of consolidations with filtering and sorting capabilities.

**Access**: 
- **Admin users**: Can access all consolidations
- **Client users**: Can only access their own consolidations
- **Anonymous**: ❌ Denied

**Arguments:**

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `page` | Int | No | 1 | Page number for pagination |
| `pageSize` | Int | No | 10 | Number of items per page (valid: 10, 20, 50, 100) |
| `orderBy` | String | No | `-created_at` | Field to order by. Prefix with `-` for descending order |
| `status` | String | No | - | Filter by consolidation status |

**Valid `orderBy` fields:**
- `created_at` / `-created_at`
- `delivery_date` / `-delivery_date`
- `status` / `-status`

**Valid `status` values:**
- `awaiting_payment`
- `pending`
- `processing`
- `in_transit`
- `delivered`
- `cancelled`

**Example - Basic query with pagination:**

```graphql
query {
  allConsolidates(page: 1, pageSize: 10) {
    results {
      id
      description
      status
      deliveryDate
      createdAt
      client {
        fullName
        email
      }
      packages {
        barcode
        description
      }
    }
    totalCount
    page
    pageSize
    hasNext
    hasPrevious
  }
}
```

**Example - With filtering and ordering:**

```graphql
query {
  allConsolidates(
    status: "in_transit",
    orderBy: "-delivery_date",
    page: 1,
    pageSize: 20
  ) {
    results {
      id
      status
      deliveryDate
      client {
        fullName
      }
    }
    totalCount
    hasNext
  }
}
```

**Returns**: `ConsolidateConnection`

**Connection Type Fields:**
- `results`: `[ConsolidateType]` - Array of consolidate objects
- `totalCount`: `Int` - Total number of items matching the query
- `page`: `Int` - Current page number
- `pageSize`: `Int` - Number of items per page
- `hasNext`: `Boolean` - Whether there is a next page
- `hasPrevious`: `Boolean` - Whether there is a previous page

**Errors:**
- `ValueError`: If `pageSize` is not one of [10, 20, 50, 100]
- `ValueError`: If `orderBy` field is not valid
- `PermissionDenied`: If user is not authenticated or lacks access

---

#### `consolidateById`

Returns a single consolidation by ID.

**Access**: 
- **Admin users**: Can access any consolidation
- **Client users**: Can only access their own consolidations
- Returns `PermissionDenied` error if user attempts to access another client's consolidation

**Arguments:**

| Argument | Type | Required | Descrip4tion     |
|----------|------|----------|------------------|
| `id` | ID | Yes | Consolidation ID |

```graphql
query {
  consolidateById(id: 1) {
    id
    description
    status
    comment
    extraAttributes
    deliveryDate
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
    }
  }
}
```

**Returns**: `ConsolidateType` or `null` if not found

---

## Dashboard

### `dashboard`

Returns dashboard statistics and recent items. Data is filtered based on user type.

**Access**: Any authenticated user

**Data Visibility:**

| Data | Admin Users | Regular Users |
|------|-------------|---------------|
| Package Stats | All packages | Own packages only |
| Consolidation Stats | All consolidations | Own consolidations only |
| Financial Stats | All packages | Returns 0 (hidden) |
| Client Count | All clients | Returns 0 (hidden) |
| Recent Packages | All recent packages | Own recent packages only |
| Recent Consolidations | All recent consolidations | Own recent consolidations only |

**Arguments:**

| Argument | Type | Required | Default | Description |
|----------|------|----------|---------|-------------|
| `recentPackages(limit: Int)` | Int | No | 5 | Number of recent packages to return |
| `recentConsolidations(limit: Int)` | Int | No | 5 | Number of recent consolidations to return |

```graphql
query {
  dashboard {
    stats {
      totalPackages
      recentPackages
      packagesPending
      packagesInTransit
      packagesDelivered
      totalConsolidations
      consolidationsPending
      consolidationsProcessing
      consolidationsInTransit
      consolidationsAwaitingPayment
      totalRealPrice
      totalServicePrice
      totalClients
    }
    recentPackages(limit: 5) {
      id
      barcode
      description
      realPrice
      servicePrice
      client {
        fullName
      }
    }
    recentConsolidations(limit: 5) {
      id
      description
      status
      deliveryDate
      packages {
        barcode
      }
    }
  }
}
```

**Returns**: `DashboardType`

**Errors:**
- `PermissionDenied`: If user is not authenticated

---

## Mutations

### Authentication Mutations

#### `emailAuth`

Authenticates a user with email and password, returns JWT token.

**Access**: Public (no authentication required)

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `email` | String | Yes | User email |
| `password` | String | Yes | User password |

```graphql
mutation {
  emailAuth(email: "user@example.com", password: "password") {
    token
    refreshToken
    payload
    refreshExpiresIn
  }
}
```

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `token` | String | JWT access token (short-lived) |
| `refreshToken` | String | Refresh token (long-lived, used to obtain new access tokens) |
| `payload` | GenericScalar | Token payload (includes email, username, exp) |
| `refreshExpiresIn` | Int | Refresh token expiration in seconds |

**Errors:**
- `GraphQLError("Invalid credentials")`: Invalid email or password

---

#### `forgotPassword`

Sends a password reset email to the user.

**Access**: Public (no authentication required)

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `email` | String | Yes | User email |

```graphql
mutation {
  forgotPassword(email: "user@example.com") {
    ok
  }
}
```

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `ok` | Boolean | Always true (to prevent user enumeration) |

**Notes:**
- Returns `ok: true` even if email doesn't exist (security measure)
- Reset link format: `http://localhost:3000/reset-password?uid=<uidb64>&token=<token>`
- Email sent via Django-Q async queue

---

#### `resetPassword`

Resets user password using token from forgot password email.

**Access**: Public (no authentication required)

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `uidb64` | String | Yes | Base64 encoded user ID |
| `token` | String | Yes | Password reset token |
| `password` | String | Yes | New password |

```graphql
mutation {
  resetPassword(
    uidb64: "MQ"
    token: "abc123..."
    password: "newpassword123"
  ) {
    ok
  }
}
```

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `ok` | Boolean | True if password reset successfully |

**Errors:**
- `GraphQLError("Invalid password reset link.")`: Invalid token or user

---

#### `refreshWithToken`

Refreshes JWT access token using a refresh token string. Returns a new access token and a new refresh token (implements token rotation).

**Access**: Public (no authentication required)

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `refreshToken` | String | Yes | The refresh token string obtained from login |

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

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `token` | String | New JWT access token (short-lived, 5 minutes) |
| `refreshToken` | String | New refresh token (old one is revoked) |
| `payload` | GenericScalar | Token payload (includes email, username, exp) |
| `refreshExpiresIn` | Int | Refresh token expiration in seconds (7 days) |

**Errors:**
- `GraphQLError("Invalid refresh token")`: Token not found in database
- `GraphQLError("Refresh token has expired")`: Token has expired
- `GraphQLError("Refresh token has been revoked")`: Token was previously revoked

**Security Notes:**
- Implements automatic token rotation (old refresh token is revoked when new one is issued)
- Store refresh tokens securely on the client (e.g., secure storage, not localStorage)
- Use the new refresh token for subsequent refresh requests

**Example Workflow:**
1. User logs in via `emailAuth` mutation
2. Client stores both `token` (access token) and `refreshToken`
3. When access token expires (after 5 minutes), call `refreshWithToken` with the refresh token
4. Client updates stored tokens with the new values
5. Old refresh token is automatically invalidated

---

#### `revokeToken`

Revokes the current refresh token (logout).

**Access**: Authenticated users only

```graphql
mutation {
  revokeToken {
    revoked
  }
}
```

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `revoked` | Boolean | True if token was revoked |

**Errors:**
- `GraphQLError("User is not authenticated.")`: User not logged in
- `GraphQLError("Refresh token not found in cookies.")`: No refresh token cookie
- `GraphQLError("Refresh token not found.")`: Token not found in database

---

#### `tokenAuth` (Standard JWT)

Standard graphql-jwt token authentication.

**Access**: Public

```graphql
mutation {
  tokenAuth(email: "user@example.com", password: "password") {
    token
    payload
    refreshExpiresIn
  }
}
```

---

#### `verifyToken`

Verifies if a JWT token is valid.

**Access**: Public

```graphql
mutation {
  verifyToken(token: "<token>") {
    payload
  }
}
```

---

#### `refreshToken`

Refreshes an expired JWT token.

**Access**: Public

```graphql
mutation {
  refreshToken(token: "<token>") {
    token
    payload
    refreshExpiresIn
  }
}
```

---

### Client Mutations

#### `createClient`

Creates a new client with associated user account.

**Access**: Superuser only

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `firstName` | String | Yes | First name |
| `lastName` | String | Yes | Last name |
| `email` | String | Yes | Email address |
| `identificationNumber` | String | No | ID/Document number |
| `state` | String | No | State/Province |
| `city` | String | No | City |
| `mainStreet` | String | No | Main street |
| `secondaryStreet` | String | No | Secondary street |
| `buildingNumber` | String | No | Building number |
| `mobilePhoneNumber` | String | No | Mobile phone |
| `phoneNumber` | String | No | Landline phone |

```graphql
mutation {
  createClient(
    firstName: "John"
    lastName: "Doe"
    email: "john@example.com"
    identificationNumber: "123456789"
    state: "California"
    city: "Los Angeles"
    mainStreet: "Main St"
    mobilePhoneNumber: "+1234567890"
  ) {
    client {
      id
      fullName
      email
      user {
        id
        email
        isActive
      }
    }
  }
}
```

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `client` | ClientType | Created client object |

**Notes:**
- A user account is automatically created with the email
- Password is auto-generated (random 16-character token)
- New user accounts are created with `isActive: false`

**Errors:**
- `PermissionDenied`: If user is not superuser

---

#### `updateClient`

Updates an existing client's information.

**Access**: Superuser (any client) or own client record

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | ID | Yes | Client ID |
| `firstName` | String | No | First name |
| `lastName` | String | No | Last name |
| `identificationNumber` | String | No | ID/Document number |
| `state` | String | No | State/Province |
| `city` | String | No | City |
| `mainStreet` | String | No | Main street |
| `secondaryStreet` | String | No | Secondary street |
| `buildingNumber` | String | No | Building number |
| `mobilePhoneNumber` | String | No | Mobile phone |
| `phoneNumber` | String | No | Landline phone |

```graphql
mutation {
  updateClient(
    id: 1
    firstName: "Jane"
    city: "San Francisco"
  ) {
    client {
      id
      fullName
      city
    }
  }
}
```

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `client` | ClientType | Updated client object |

**Notes:**
- `email` and `user` cannot be modified through this mutation

**Errors:**
- `PermissionDenied`: If regular user tries to update another client

---

#### `deleteClient`

Deletes a client and associated user account.

**Access**: Superuser only

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | ID | Yes | Client ID |

```graphql
mutation {
  deleteClient(id: 1) {
    ok
  }
}
```

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `ok` | Boolean | True if deleted successfully |

**Errors:**
- `PermissionDenied`: If user is not superuser

---

### Package Mutations

#### `createPackage`

Creates a new package for a client.

**Access**: Superuser only

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `barcode` | String | Yes | Unique barcode |
| `courier` | String | Yes | Courier service name |
| `otherCourier` | String | No | Alternative courier |
| `length` | Float | No | Package length |
| `width` | Float | No | Package width |
| `height` | Float | No | Package height |
| `dimensionUnit` | String | No | Dimension unit |
| `weight` | Float | No | Package weight |
| `weightUnit` | String | No | Weight unit |
| `description` | String | No | Package description |
| `purchaseLink` | String | No | Purchase receipt URL |
| `realPrice` | Float | No | Actual price |
| `servicePrice` | Float | No | Service price |
| `arrivalDate` | Date | No | Arrival date |
| `comments` | String | No | Comments |
| `clientId` | ID | Yes | Client ID (owner) |

```graphql
mutation {
  createPackage(
    barcode: "PKG123456"
    courier: "FedEx"
    description: "Electronics"
    weight: 2.5
    weightUnit: "kg"
    realPrice: 150.00
    clientId: 1
  ) {
    package {
      id
      barcode
      courier
      description
      client {
        fullName
      }
    }
  }
}
```

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `package` | PackageType | Created package object |

**Errors:**
- `PermissionDenied`: If user is not superuser
- `ValidationError`: If client doesn't exist

---

#### `updatePackage`

Updates an existing package.

**Access**: Superuser only

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | ID | Yes | Package ID |
| `courier` | String | No | Courier service name |
| `otherCourier` | String | No | Alternative courier |
| `length` | Float | No | Package length |
| `width` | Float | No | Package width |
| `height` | Float | No | Package height |
| `dimensionUnit` | String | No | Dimension unit |
| `weight` | Float | No | Package weight |
| `weightUnit` | String | No | Weight unit |
| `description` | String | No | Package description |
| `purchaseLink` | String | No | Purchase receipt URL |
| `realPrice` | Float | No | Actual price |
| `servicePrice` | Float | No | Service price |
| `arrivalDate` | Date | No | Arrival date |
| `comments` | String | No | Comments |
| `clientId` | ID | No | New client ID (only if not consolidated) |

```graphql
mutation {
  updatePackage(
    id: 1
    description: "Updated description"
    servicePrice: 25.00
  ) {
    package {
      id
      barcode
      description
      servicePrice
    }
  }
}
```

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `package` | PackageType | Updated package object |

**Restrictions:**
- `barcode` cannot be modified
- `clientId` can only be changed if package is not part of a consolidation

**Errors:**
- `PermissionDenied`: If user is not superuser
- `ValidationError`: If package not found, barcode modification attempted, or client change on consolidated package

---

#### `deletePackage`

Deletes a package.

**Access**: Superuser only

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | ID | Yes | Package ID |

```graphql
mutation {
  deletePackage(id: 1) {
    success
  }
}
```

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `success` | Boolean | True if deleted successfully |

**Restrictions:**
- Cannot delete packages that are part of a consolidation

**Errors:**
- `PermissionDenied`: If user is not superuser
- `ValidationError`: If package not found or package belongs to a consolidation

---

### Consolidate Mutations

#### `createConsolidate`

Creates a new consolidation grouping multiple packages.

**Access**: Superuser only

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `description` | String | Yes | Consolidation description |
| `status` | String | Yes | Initial status |
| `packageIds` | [ID] | Yes | List of package IDs to consolidate |
| `deliveryDate` | Date | No | Expected delivery date |
| `comment` | String | No | Comments |
| `sendEmail` | Boolean | No | Send notification email (default: false) |

**Valid Initial Statuses:**
- `awaiting_payment`
- `pending`
- `processing`

```graphql
mutation {
  createConsolidate(
    description: "Consolidation for John Doe"
    status: "pending"
    packageIds: [1, 2, 3]
    deliveryDate: "2024-12-25"
    comment: "Handle with care"
    sendEmail: true
  ) {
    consolidate {
      id
      description
      status
      client {
        fullName
        email
      }
      packages {
        barcode
      }
    }
  }
}
```

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `consolidate` | ConsolidateType | Created consolidation object |

**Validation Rules:**
- All packages must exist
- All packages must belong to the same client
- No package can already belong to another consolidation
- Status must be a valid Consolidate status
- Initial status must be `awaiting_payment`, `pending`, or `processing`

**Errors:**
- `PermissionDenied`: If user is not superuser
- `ValidationError`: For any validation failure

---

#### `updateConsolidate`

Updates an existing consolidation.

**Access**: Superuser only

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | ID | Yes | Consolidation ID |
| `description` | String | No | Description |
| `status` | String | No | New status (see status transitions) |
| `deliveryDate` | Date | No | Delivery date |
| `comment` | String | No | Comments |
| `packageIds` | [ID] | No | New list of package IDs |

```graphql
mutation {
  updateConsolidate(
    id: 1
    status: "in_transit"
    comment: "Shipped via FedEx"
  ) {
    consolidate {
      id
      status
      comment
      packages {
        barcode
      }
    }
  }
}
```

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `consolidate` | ConsolidateType | Updated consolidation object |

**Status Transition Rules:**

| Current Status | Allowed Transitions |
|----------------|---------------------|
| `awaiting_payment` | `pending`, `cancelled` |
| `pending` | `processing`, `cancelled` |
| `processing` | `in_transit`, `cancelled` |
| `in_transit` | `delivered`, `cancelled` |
| `delivered` | (none) |
| `cancelled` | (none) |

**Notes:**
- `client` cannot be modified
- `extraAttributes` is ignored (not modifiable via this mutation)
- When updating `packageIds`, all new packages must belong to the same client

**Errors:**
- `PermissionDenied`: If user is not superuser
- `ValidationError`: For invalid status transitions or package validation

---

#### `deleteConsolidate`

Deletes a consolidation.

**Access**: Superuser only

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | ID | Yes | Consolidation ID |

```graphql
mutation {
  deleteConsolidate(id: 1) {
    success
  }
}
```

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `success` | Boolean | True if deleted, false if not found |

**Notes:**
- Deleting a consolidation does not delete associated packages
- Packages become "unconsolidated" and can be added to other consolidations

**Errors:**
- `PermissionDenied`: If user is not superuser

---

### User Mutations

#### `deleteUser`

Deletes a user account.

**Access**: Superuser only

**Arguments:**

| Argument | Type | Required | Description |
|----------|------|----------|-------------|
| `id` | ID | Yes | User ID |

```graphql
mutation {
  deleteUser(id: 1) {
    ok
  }
}
```

**Returns:**

| Field | Type | Description |
|-------|------|-------------|
| `ok` | Boolean | True if deleted successfully |

**Errors:**
- `PermissionDenied`: If user is not superuser

---

## User Permissions

### Permission Matrix

| Operation | Superuser | Regular User | Anonymous |
|-----------|-----------|--------------|-----------|
| **Queries** ||||
| `me` | ✅ | ✅ | ❌ |
| `dashboard` | All data | Own data | ❌ |
| `allClients` | ✅ | ❌ | ❌ |
| `client` | Any | Own only | ❌ |
| `allPackages` | All + filter by client | Own only | ❌ |
| `package` | Any | Own only | ❌ |
| `allConsolidates` | All consolidates | Own only | ❌ |
| `consolidateById` | Any | Own only | ❌ |
| **Mutations** ||||
| `emailAuth` | ✅ | ✅ | ✅ |
| `forgotPassword` | ✅ | ✅ | ✅ |
| `resetPassword` | ✅ | ✅ | ✅ |
| `revokeToken` | ✅ | ✅ | ❌ |
| `tokenAuth` | ✅ | ✅ | ✅ |
| `verifyToken` | ✅ | ✅ | ✅ |
| `refreshToken` | ✅ | ✅ | ✅ |
| `createClient` | ✅ | ❌ | ❌ |
| `updateClient` | Any | Own only | ❌ |
| `deleteClient` | ✅ | ❌ | ❌ |
| `createPackage` | ✅ | ❌ | ❌ |
| `updatePackage` | ✅ | ❌ | ❌ |
| `deletePackage` | ✅ | ❌ | ❌ |
| `createConsolidate` | ✅ | ❌ | ❌ |
| `updateConsolidate` | ✅ | ❌ | ❌ |
| `deleteConsolidate` | ✅ | ❌ | ❌ |
| `deleteUser` | ✅ | ❌ | ❌ |

**Legend:**
- ✅ Allowed
- ❌ Denied (PermissionDenied error)
- Any: Can access all records
- Own only: Can only access own records
- All + filter: Can access all and filter by client

---

## Error Handling

### Common Error Types

#### PermissionDenied

Returned when a user attempts an operation they are not authorized for.

```json
{
  "errors": [
    {
      "message": "You do not have permission to perform this action.",
      "extensions": {
        "code": "PERMISSION_DENIED"
      }
    }
  ]
}
```

#### ValidationError

Returned when input data fails validation rules.

```json
{
  "errors": [
    {
      "message": "The provided client does not exist.",
      "extensions": {
        "code": "VALIDATION_ERROR"
      }
    }
  ]
}
```

#### GraphQLError (Authentication)

Returned for authentication failures.

```json
{
  "errors": [
    {
      "message": "Invalid credentials",
      "extensions": {
        "code": "GRAPHQL_ERROR"
      }
    }
  ]
}
```

### Error Codes Reference

| Error Message | Context | HTTP Status |
|---------------|---------|-------------|
| `Invalid credentials` | Wrong email/password in `emailAuth` | 200 (GraphQL) |
| `User is not authenticated.` | Calling `revokeToken` while logged out | 200 (GraphQL) |
| `Refresh token not found in cookies.` | Missing refresh token | 200 (GraphQL) |
| `Invalid password reset link.` | Invalid/expired reset token | 200 (GraphQL) |
| `You do not have permission to perform this action.` | Permission denied | 200 (GraphQL) |
| `You do not have permission to view this resource.` | Query permission denied | 200 (GraphQL) |
| `The provided client does not exist.` | Invalid client_id | 200 (GraphQL) |
| `Package not found.` | Invalid package id | 200 (GraphQL) |
| `Barcode cannot be modified.` | Attempting to change barcode | 200 (GraphQL) |
| `Client cannot be updated for packages already consolidated.` | Client change on consolidated package | 200 (GraphQL) |
| `Package cannot be deleted because it belongs to a consolidate.` | Deleting consolidated package | 200 (GraphQL) |
| `At least one package ID is required.` | Empty package_ids list | 200 (GraphQL) |
| `One or more packages do not exist.` | Invalid package IDs | 200 (GraphQL) |
| `All packages must belong to the same client.` | Cross-client consolidation | 200 (GraphQL) |
| `Package already belongs to a consolidate.` | Package already consolidated | 200 (GraphQL) |
| `Invalid status: '<status>' is not a valid Consolidate status.` | Invalid status value | 200 (GraphQL) |
| `Invalid initial status: a new consolidate cannot start as '<status>'.` | Wrong initial status | 200 (GraphQL) |
| `Invalid status transition from '<current>' to '<new>'.` | Invalid status change | 200 (GraphQL) |
| `Package <id> already belongs to another consolidate.` | Package in another consolidation | 200 (GraphQL) |
| `Invalid page_size. Valid values are 10, 20, 50, 100.` | Wrong pagination size | 200 (GraphQL) |
| `Invalid order_by value.` | Invalid sort field | 200 (GraphQL) |

---

## Example Workflows

### Complete Authentication Flow

```graphql
# 1. Login
mutation Login {
  emailAuth(email: "admin@example.com", password: "adminpass") {
    token
    refreshToken
    payload
    refreshExpiresIn
  }
}

# 2. Access protected query with Authorization: JWT <access_token> header
query GetMyInfo {
  me {
    id
    email
    isSuperuser
  }
}

# 3. Refresh access token when expired (use refreshToken, not access token)
mutation Refresh {
  refreshToken(token: "<refresh_token>") {
    token
    payload
  }
}

# 4. Logout
mutation Logout {
  revokeToken {
    revoked
  }
}
```

### Admin Creating a Complete Order Flow

```graphql
# 1. Create a client
mutation CreateClient {
  createClient(
    firstName: "Alice"
    lastName: "Smith"
    email: "alice@example.com"
    mobilePhoneNumber: "+1234567890"
  ) {
    client {
      id
      fullName
    }
  }
}

# 2. Create packages for the client
mutation CreatePackages {
  pkg1: createPackage(
    barcode: "PKG001"
    courier: "DHL"
    description: "Laptop"
    weight: 2.0
    weightUnit: "kg"
    realPrice: 1000.00
    clientId: 1
  ) {
    package {
      id
      barcode
    }
  }
  
  pkg2: createPackage(
    barcode: "PKG002"
    courier: "DHL"
    description: "Mouse"
    weight: 0.2
    weightUnit: "kg"
    realPrice: 50.00
    clientId: 1
  ) {
    package {
      id
      barcode
    }
  }
}

# 3. Create a consolidation
mutation CreateConsolidation {
  createConsolidate(
    description: "Alice's tech order"
    status: "pending"
    packageIds: [1, 2]
    sendEmail: true
  ) {
    consolidate {
      id
      status
      packages {
        barcode
      }
    }
  }
}

# 4. Update consolidation status as it progresses
mutation UpdateStatus {
  updateConsolidate(
    id: 1
    status: "in_transit"
    comment: "Shipped today"
  ) {
    consolidate {
      id
      status
      comment
    }
  }
}
```

### Client Viewing Their Data

```graphql
# Regular user can only see their own data
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
      status
      consolidate {
        id
        status
      }
    }
  }
}
```
