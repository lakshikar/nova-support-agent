# NovaTech Platform — API Reference (Excerpts)

**API Version:** v2  
**Base URL:** `https://{your-instance}.novatech.com/api/v2`  
**Authentication:** API Key (header: `X-Api-Key`) or OAuth 2.0 Bearer Token  
**Content Type:** `application/json`  
**Last Updated:** May 10, 2024

---

## Asset Lifecycle API

### List Assets

```
GET /api/v2/assets
```

Retrieves a paginated list of assets.

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `cursor` | string | No | Pagination cursor from previous response |
| `limit` | integer | No | Items per page (default: 50, max: 500) |
| `status` | string | No | Filter by status: `active`, `disposed`, `maintenance`, `decommissioned` |
| `module` | string | No | Filter by module: `asset-lifecycle`, `field-service`, `supply-chain` |
| `search` | string | No | Search across asset name, tag, and custom fields |
| `category` | string | No | Filter by asset category ID |

**Response (200 OK):**

```json
{
  "data": [
    {
      "id": "AST-10042",
      "name": "Industrial Generator Unit 7",
      "category": "Power Generation",
      "status": "active",
      "location": "Plant B - Section 4",
      "inServiceDate": "2019-03-15",
      "currentValue": 245000.00,
      "depreciationMethod": "straight-line",
      "healthScore": 72,
      "lastMaintenanceDate": "2024-04-10",
      "modules": ["asset-lifecycle", "field-service"]
    }
  ],
  "nextCursor": "eyJpZCI6IkFTVC0xMDA0MyJ9",
  "totalCount": 15234
}
```

---

### Get Asset by ID

```
GET /api/v2/assets/{assetId}
```

Retrieves detailed information for a specific asset.

**Response (200 OK):**

```json
{
  "id": "AST-10042",
  "name": "Industrial Generator Unit 7",
  "category": "Power Generation",
  "status": "active",
  "location": "Plant B - Section 4",
  "inServiceDate": "2019-03-15",
  "purchasePrice": 500000.00,
  "currentValue": 245000.00,
  "salvageValue": 50000.00,
  "usefulLifeYears": 15,
  "depreciationMethod": "straight-line",
  "depreciationScheduleId": "DS-001",
  "healthScore": 72,
  "lastMaintenanceDate": "2024-04-10",
  "nextScheduledMaintenance": "2024-07-10",
  "modules": ["asset-lifecycle", "field-service"],
  "customFields": {
    "manufacturer": "PowerGen Corp",
    "serialNumber": "PG-2019-07742",
    "warrantyExpiry": "2024-03-15"
  },
  "metadata": {
    "createdAt": "2019-03-15T10:00:00Z",
    "updatedAt": "2024-04-10T14:30:00Z",
    "createdBy": "admin@meridian.com",
    "lastSyncedAt": "2024-05-20T08:15:00Z"
  }
}
```

---

### Get Asset Health Score

```
GET /api/v2/assets/{assetId}/health-score
```

Retrieves the AI-powered health score for an asset (v24.2+).

**Response (200 OK):**

```json
{
  "assetId": "AST-10042",
  "healthScore": 72,
  "components": {
    "age": 65,
    "maintenanceHistory": 80,
    "failureRate": 75,
    "utilization": 68
  },
  "trend": "declining",
  "recommendation": "Schedule preventive maintenance within 30 days",
  "calculatedAt": "2024-05-20T08:00:00Z"
}
```

---

### Generate Depreciation Report (v24.2 — New Engine)

```
POST /api/v2/reports/generate
```

Generates a report using the new v24.2 reporting engine.

**Request Body:**

```json
{
  "reportType": "quarterly-depreciation",
  "parameters": {
    "fiscalQuarter": "2024-Q1",
    "assetCategories": ["all"],
    "includeDisposed": false,
    "groupBy": "category"
  },
  "outputFormat": "pdf",
  "async": true
}
```

**Response (202 Accepted):**

```json
{
  "reportId": "RPT-20240520-001",
  "status": "queued",
  "estimatedCompletionTime": "2024-05-20T08:15:00Z",
  "statusUrl": "/api/v2/reports/RPT-20240520-001/status"
}
```

> ⚠️ **Known Issue (NT-4523):** This endpoint may return a 500 error with code NT-4523 when generating quarterly depreciation reports that use custom depreciation schedules created before v24.1. Use the legacy endpoint as a workaround (see below).

---

### Generate Depreciation Report (Legacy Engine — Workaround)

```
GET /api/v1/reports/depreciation
```

> ⚠️ **Deprecated:** This endpoint uses the legacy reporting engine from v24.1. It will be removed in v25.1. Use as a temporary workaround for NT-4523.

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `quarter` | string | Yes | Fiscal quarter (e.g., `2024-Q1`) |
| `format` | string | No | `legacy` (default), `pdf`, `excel` |
| `categories` | string | No | Comma-separated asset category IDs |

**Response (200 OK):**

Returns the report file directly as a binary download.

```
Content-Type: application/pdf
Content-Disposition: attachment; filename="depreciation-report-2024-Q1.pdf"
```

---

### Check Report Status

```
GET /api/v2/reports/{reportId}/status
```

Checks the status of an asynchronously generated report.

**Response (200 OK):**

```json
{
  "reportId": "RPT-20240520-001",
  "status": "completed",
  "completedAt": "2024-05-20T08:14:32Z",
  "downloadUrl": "/api/v2/reports/RPT-20240520-001/download",
  "expiresAt": "2024-05-27T08:14:32Z",
  "metadata": {
    "rowCount": 15234,
    "fileSize": "2.4 MB",
    "generationTime": "42 seconds"
  }
}
```

**Possible Statuses:** `queued`, `processing`, `completed`, `failed`

If status is `failed`:

```json
{
  "reportId": "RPT-20240520-002",
  "status": "failed",
  "error": {
    "code": "NT-4523",
    "message": "Depreciation schedule format incompatible with reporting engine v2",
    "details": "Custom schedule DS-LEGACY-003 uses annual rate format. Migration required."
  }
}
```

---

## Ticket Management API

### Create Ticket

```
POST /api/v2/tickets
```

**Request Body:**

```json
{
  "subject": "Error NT-4523 when generating asset report",
  "body": "We're getting error NT-4523 every time we try to generate the quarterly asset depreciation report.",
  "customer": "Meridian Energy",
  "supportTier": "premium",
  "severity": "high",
  "module": "asset-lifecycle",
  "tags": ["reporting", "depreciation", "v24.2"],
  "attachments": []
}
```

**Response (201 Created):**

```json
{
  "ticketId": "TK-20253",
  "status": "new",
  "createdAt": "2024-05-20T09:00:00Z",
  "sla": {
    "responseDeadline": "2024-05-20T13:00:00Z",
    "resolutionDeadline": "2024-05-27T09:00:00Z"
  }
}
```

---

### Get Ticket by ID

```
GET /api/v2/tickets/{ticketId}
```

**Response (200 OK):**

```json
{
  "ticketId": "TK-20248",
  "subject": "Field service scheduling conflicts",
  "body": "We're seeing scheduling conflicts for work orders at our main plant...",
  "customer": "Atlas Manufacturing",
  "supportTier": "standard",
  "severity": "high",
  "status": "in-progress",
  "module": "field-service",
  "createdAt": "2024-05-19T14:00:00Z",
  "lastUpdatedAt": "2024-05-22T10:30:00Z",
  "assignedTo": "Sarah Chen",
  "sla": {
    "responseDeadline": "2024-05-20T14:00:00Z",
    "resolutionDeadline": "2024-06-03T14:00:00Z",
    "responseStatus": "met",
    "resolutionStatus": "in-progress"
  },
  "relatedTickets": ["TK-20251"],
  "tags": ["scheduling", "field-service", "v24.2"],
  "history": [
    {
      "timestamp": "2024-05-19T14:00:00Z",
      "action": "created",
      "actor": "Atlas Manufacturing (portal)"
    },
    {
      "timestamp": "2024-05-19T16:30:00Z",
      "action": "assigned",
      "actor": "system",
      "details": "Assigned to Sarah Chen"
    },
    {
      "timestamp": "2024-05-20T09:15:00Z",
      "action": "response_sent",
      "actor": "Sarah Chen",
      "details": "Initial assessment provided. Linked to known issue KI-2402-003."
    }
  ]
}
```

---

### Search Tickets

```
GET /api/v2/tickets/search
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `q` | string | No | Full-text search across subject and body |
| `customer` | string | No | Filter by customer name |
| `status` | string | No | Filter: `new`, `triaged`, `in-progress`, `pending-customer`, `pending-engineering`, `resolved`, `closed` |
| `severity` | string | No | Filter: `critical`, `high`, `medium`, `low` |
| `module` | string | No | Filter by module name |
| `createdAfter` | datetime | No | Filter tickets created after this date |
| `createdBefore` | datetime | No | Filter tickets created before this date |
| `cursor` | string | No | Pagination cursor |
| `limit` | integer | No | Items per page (default: 50) |

**Response (200 OK):**

```json
{
  "data": [
    {
      "ticketId": "TK-20248",
      "subject": "Field service scheduling conflicts",
      "customer": "Atlas Manufacturing",
      "severity": "high",
      "status": "in-progress",
      "createdAt": "2024-05-19T14:00:00Z"
    }
  ],
  "nextCursor": "eyJ0aWNrZXRJZCI6IlRLLTIwMjQ5In0=",
  "totalCount": 142
}
```

---

## Field Service API

### List Work Orders

```
GET /api/v2/work-orders
```

**Query Parameters:**

| Parameter | Type | Required | Description |
|---|---|---|---|
| `status` | string | No | Filter: `scheduled`, `in-progress`, `completed`, `cancelled` |
| `technicianId` | string | No | Filter by assigned technician |
| `customerId` | string | No | Filter by customer |
| `scheduledDate` | date | No | Filter by scheduled date |
| `cursor` | string | No | Pagination cursor |

---

### Trigger Schedule Optimization

```
POST /api/v2/field-service/schedule/optimize
```

Triggers the scheduling algorithm to optimize work order assignments.

**Request Body:**

```json
{
  "scope": "full",
  "dateRange": {
    "start": "2024-05-20",
    "end": "2024-05-24"
  },
  "constraints": {
    "respectExistingAssignments": true,
    "maxTravelTimeMinutes": 60
  },
  "dryRun": false
}
```

**Response (202 Accepted):**

```json
{
  "optimizationId": "OPT-20240520-001",
  "status": "running",
  "estimatedCompletionTime": "2024-05-20T08:10:00Z",
  "statusUrl": "/api/v2/field-service/schedule/optimize/OPT-20240520-001/status"
}
```

---

## Sync Management API

### Trigger Manual Sync

```
POST /api/v2/assets/sync/trigger
```

Triggers a manual synchronization of asset data across modules.

> 💡 **Use this endpoint** as a workaround for sync failures (KI-2402-004).

**Request Body:**

```json
{
  "syncType": "full",
  "modules": ["asset-lifecycle", "field-service", "supply-chain"],
  "options": {
    "conflictResolution": "source-priority",
    "sourcePriorityModule": "asset-lifecycle",
    "forceOverwrite": false
  }
}
```

**Response (202 Accepted):**

```json
{
  "syncId": "SYNC-20240520-001",
  "status": "running",
  "estimatedCompletionTime": "2024-05-20T08:30:00Z",
  "affectedAssets": 15234,
  "statusUrl": "/api/v2/assets/sync/SYNC-20240520-001/status"
}
```

---

### Get Sync Status

```
GET /api/v2/assets/sync/{syncId}/status
```

**Response (200 OK):**

```json
{
  "syncId": "SYNC-20240520-001",
  "status": "completed",
  "startedAt": "2024-05-20T08:15:00Z",
  "completedAt": "2024-05-20T08:28:45Z",
  "results": {
    "totalAssets": 15234,
    "synced": 15210,
    "failed": 24,
    "conflicts": 8,
    "conflictsResolved": 6,
    "conflictsPending": 2
  }
}
```

---

### Get Sync Health

```
GET /api/v2/assets/sync/health
```

Returns current sync health metrics.

**Response (200 OK):**

```json
{
  "overallHealth": "degraded",
  "modulePairs": [
    {
      "source": "asset-lifecycle",
      "target": "field-service",
      "status": "healthy",
      "latency": "12 seconds",
      "failedEventsLast24h": 2
    },
    {
      "source": "asset-lifecycle",
      "target": "supply-chain",
      "status": "degraded",
      "latency": "45 seconds",
      "failedEventsLast24h": 18
    },
    {
      "source": "field-service",
      "target": "supply-chain",
      "status": "healthy",
      "latency": "8 seconds",
      "failedEventsLast24h": 0
    }
  ],
  "lastFullSync": "2024-05-19T02:00:00Z",
  "activeConflicts": 2
}
```

---

## Common API Error Response Format

All API errors follow a consistent format:

```json
{
  "error": {
    "code": "NT-XXXX",
    "message": "Human-readable error description",
    "details": "Additional context or troubleshooting guidance",
    "traceId": "abc123-def456-ghi789",
    "timestamp": "2024-05-20T08:15:32Z"
  }
}
```

The `traceId` can be provided to NovaTech Support for advanced troubleshooting.

---

## API Versioning

| Version | Status | End of Life |
|---|---|---|
| v1 | Deprecated (legacy compatibility only) | January 2025 (v25.1) |
| v2 | Current | — |

All new integrations should use API v2. API v1 endpoints are maintained only for backward compatibility and will not receive new features.

---

*For the complete API reference, visit [docs.novatech.com/api](https://docs.novatech.com/api). For API support, contact api-support@novatech.com.*
