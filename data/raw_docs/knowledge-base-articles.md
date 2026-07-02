# NovaTech Platform — Knowledge Base Articles

**Last Updated:** May 15, 2024

---

## KB-001: Understanding Asset Depreciation in NovaTech

**Last Updated:** September 12, 2023  
**Applies To:** NovaTech Platform v23.x, v24.1  
**Category:** Asset Lifecycle

> ⚠️ **Note:** This article was written for v23.x and v24.1. Some information may not apply to v24.2 due to the reporting engine overhaul. See release notes for v24.2 for details on the new reporting engine.

### Overview

NovaTech Platform supports three standard depreciation methods:

1. **Straight-Line Depreciation:** Equal depreciation amount each period over the asset's useful life.
2. **Declining Balance Depreciation:** Accelerated depreciation with a fixed percentage applied to the remaining book value each period.
3. **Sum-of-Years-Digits (SYD):** Accelerated depreciation where the annual rate decreases over the asset's useful life.

### Custom Depreciation Schedules

In addition to the three standard methods, administrators can create **custom depreciation schedules** for assets with unique depreciation requirements (e.g., assets with seasonal usage patterns, assets with regulatory depreciation rules).

Custom depreciation schedules support:
- Custom period lengths (monthly, quarterly, annual)
- Manual rate adjustments for specific periods
- Mid-year convention rules (half-year, mid-quarter, mid-month)
- Salvage value calculations

**Creating a Custom Schedule (v23.x / v24.1):**

1. Navigate to Admin Console > Asset Lifecycle > Depreciation Schedules
2. Click "Create Custom Schedule"
3. Enter the schedule name, method, and parameters
4. Define rate table with period-specific adjustments
5. Set mid-year convention rules
6. Save and assign to asset categories

### Quarterly Depreciation Report

The quarterly depreciation report summarizes:
- Beginning book value for each asset
- Depreciation charges for the quarter
- Accumulated depreciation
- Ending book value
- Comparison to forecast

**To generate the report (v23.x / v24.1):**

1. Navigate to Reports > Asset Lifecycle > Quarterly Depreciation
2. Select the fiscal quarter and asset categories
3. Choose output format (PDF or Excel)
4. Click "Generate"

> **Note:** Report generation may take several minutes for large asset registries (>50,000 assets). The system queues the report and sends an email notification when it's ready.

### Common Issues

- **Report shows $0 depreciation for some assets:** Check that the asset's "in service" date is before the report quarter's start date.
- **Rounding differences between quarterly and annual reports:** This is expected and is due to monthly vs. annual rate calculations. Differences should be less than $1 per asset per year.
- **Custom schedules not appearing in dropdown:** Ensure the schedule is in "Active" status and assigned to the relevant asset category.

### Related

- Troubleshooting Guide: Error NT-4523 (report generation failures in v24.2)
- KB-003: Migrating Reports to v24.2 Format

---

## KB-002: Understanding Asset Tracking Sync in v24.2

**Last Updated:** May 10, 2024  
**Applies To:** NovaTech Platform v24.2, v24.2.1  
**Category:** Asset Tracking

### Overview

NovaTech Platform v24.2 introduced a completely new **event-driven synchronization architecture** for asset tracking. This article explains how the new sync system works, common issues, and troubleshooting steps.

### How Sync Works in v24.2

**Previous Architecture (v24.1 and earlier):**
- Batch-based sync running every 15 minutes
- Sequential processing of changes
- Single sync queue for all modules
- No conflict detection

**New Architecture (v24.2):**
- Event-driven real-time sync (latency <30 seconds)
- Parallel processing of changes across modules
- Separate event streams per module
- Conflict detection and resolution
- Full audit trail via event sourcing

### Sync Flow

```
Asset Change Detected
    ↓
Event Published to Module Event Stream
    ↓
Sync Service Consumes Event
    ↓
Conflict Detection
    ├── No Conflict → Apply Change to Target Modules
    └── Conflict Detected → Apply Resolution Strategy
                                ├── Last-Write-Wins (default)
                                ├── Source-Priority
                                └── Manual Review Queue
```

### Conflict Resolution Strategies

| Strategy | Description | Best For |
|---|---|---|
| **Last-Write-Wins** | Most recent change overwrites previous. Default strategy. | Low-conflict environments where changes are infrequent |
| **Source-Priority** | Changes from a designated "source of truth" module always win. | Environments where one module (e.g., Asset Lifecycle) is authoritative |
| **Manual Review** | Conflicting changes are queued for human review. | Highly regulated industries where data accuracy is critical |

Configure strategies at: Admin Console > Asset Tracking > Sync Rules > Conflict Resolution

### Known Issues

**Sync Failures for Assets Across 3+ Modules (KI-2402-004):**

Assets that are referenced in 3 or more modules simultaneously (e.g., Asset Lifecycle + Field Service + Supply Chain) may experience intermittent sync failures with `SyncConflictException: circular dependency detected` (error NT-5098).

**Why this happens:**
- The new sync service processes events in parallel
- When Asset A changes in Module 1, it triggers updates in Modules 2 and 3
- Those updates may trigger cascading updates back to Module 1
- The sync service detects this circular chain and stops to prevent infinite loops

**Workaround:**
1. Trigger a manual full sync: Admin Console > Asset Tracking > Sync Management > Full Sync
2. For frequently affected assets, add the problematic sync path to exclusions: Admin Console > Asset Tracking > Sync Rules > Exclusions
3. Consider using "Source-Priority" conflict resolution to establish a clear data flow direction

### Monitoring Sync Health

The Sync Health Dashboard (Admin Console > Asset Tracking > Sync Dashboard) shows:
- Real-time sync status per module pair
- Failed sync events with error details
- Sync latency metrics
- Conflict resolution statistics

**Recommended monitoring thresholds:**
- Failed sync events > 10/hour → Investigate
- Sync latency > 60 seconds → Check system load
- Conflict rate > 5% → Review data model and sync rules

### Related

- Troubleshooting Guide: Error NT-5098 (Sync Conflict Exception)
- Known Issues: KI-2402-004

---

## KB-003: Migrating Reports to v24.2 Format

**Last Updated:** May 1, 2024  
**Applies To:** NovaTech Platform v24.2  
**Category:** Asset Lifecycle / Reporting

### Overview

NovaTech Platform v24.2 introduces a new reporting engine with a different report template format. Reports created in v24.1 and earlier (legacy reports) will continue to work through the legacy compatibility layer, but should be migrated to the new format before v25.1 (when the legacy layer will be removed).

### What's Changed

| Aspect | Legacy Format (v24.1-) | New Format (v24.2+) |
|---|---|---|
| **Template storage** | XML-based | JSON-based |
| **Calculated columns** | SQL expressions | NovaTech Expression Language (NEL) |
| **Scheduling** | Cron-based | Event-driven with cron fallback |
| **Export formats** | PDF, Excel | PDF, Excel, CSV, JSON |
| **Caching** | None | Intelligent caching with auto-invalidation |
| **Depreciation data** | Annual rate percentages | Monthly rate arrays with period adjustments |

### Migration Steps

1. Open Admin Console > Reports > Migration
2. Click "Scan Legacy Reports" — the system identifies all reports needing migration
3. Review the scan results:
   - ✅ **Auto-migrateable:** Reports that can be automatically converted
   - ⚠️ **Needs Review:** Reports that can be converted but may need manual verification
   - ❌ **Manual Migration Required:** Reports with features that don't have direct equivalents
4. Click "Start Migration" for auto-migrateable reports
5. Review and test migrated reports for accuracy
6. Manually recreate reports that couldn't be auto-migrated

### Common Migration Issues

- **Custom depreciation schedules:** Reports using pre-v24.1 custom depreciation schedules may fail with error NT-4523 after migration. See Troubleshooting Guide for resolution.
- **Complex SQL expressions:** Some legacy SQL expressions don't have direct NEL equivalents. These must be rewritten manually.
- **Chart types:** Legacy "3D Pie" and "3D Bar" chart types are not available in the new engine. They are migrated to 2D equivalents.

### Timeline

- **Now through v24.3:** Both legacy and new report engines available simultaneously
- **v24.3 (July 2024):** Legacy report engine enters deprecation period (still functional but no new features)
- **v25.1 (January 2025):** Legacy report engine removed. All reports must use the new format.

### Related

- Troubleshooting Guide: Error NT-4401 (Report Template Not Found)
- Troubleshooting Guide: Error NT-4523 (Depreciation Report Failure)
- KB-001: Understanding Asset Depreciation in NovaTech

---

## KB-004: Field Service Scheduling Configuration

**Last Updated:** April 30, 2024  
**Applies To:** NovaTech Platform v24.2  
**Category:** Field Service

### Overview

NovaTech Platform v24.2 includes a completely redesigned scheduling algorithm based on constraint-based optimization. This article covers configuration best practices for the new scheduling engine.

### Scheduling Constraints

The new engine supports the following constraint types:

| Constraint Type | Description | Default Priority |
|---|---|---|
| **Technician Skills** | Match required job skills to technician certifications | Mandatory |
| **Availability Window** | Respect technician work hours and customer preferred times | Mandatory |
| **Travel Time** | Minimize travel time between consecutive jobs | High |
| **Customer Preference** | Assign preferred or previously assigned technician | Medium |
| **Parts Availability** | Ensure required parts are available before scheduling | High |
| **Certification Expiry** | Don't assign technicians with expiring certifications | Mandatory |
| **Workload Balance** | Distribute jobs evenly across available technicians | Low |

### Configuration Steps

1. Navigate to Admin Console > Field Service > Scheduling Rules
2. Review default constraints and adjust priorities as needed
3. Add custom constraints if required (e.g., language preferences, security clearance)
4. Test scheduling with a dry-run: Admin Console > Field Service > Schedule > "Dry Run"
5. Review the optimization report for constraint violations and quality scores

### Best Practices

- **Start with defaults:** The v24.2 defaults work well for most organizations. Test before customizing.
- **Limit mandatory constraints:** Too many mandatory constraints may make it impossible to schedule all work orders. The optimizer will leave unschedulable work orders unassigned.
- **Use the dry-run feature:** Always dry-run schedule changes before applying them.
- **Review same-location jobs:** Due to known issue KI-2402-003, review schedules for work orders at the same customer location within 30 minutes of each other.
- **Buffer time between jobs:** Consider adding a 15-30 minute buffer between consecutive jobs at different locations to account for unexpected delays.

### Migration from v24.1 Scheduling

If you're upgrading from v24.1:

1. Existing scheduling rules are **automatically migrated** to the new constraint format.
2. Review migrated rules — the new algorithm may interpret some rules differently.
3. Run a parallel schedule comparison (dry-run new vs. current schedule) to identify differences.
4. The new algorithm typically produces **more optimal** schedules but may assign different technicians than the old algorithm for the same jobs.
5. Allow 2-4 weeks for technicians to adjust to potentially different route patterns.

### Troubleshooting

- **NT-3200 (Scheduling Constraint Violation):** The optimizer cannot satisfy all mandatory constraints. Review which constraints are marked as mandatory and consider relaxing non-critical ones.
- **Work orders left unassigned:** Check the optimization report for the specific constraints that prevented assignment.
- **Different results each run:** The optimizer may produce different but equivalently optimal schedules. Enable "deterministic mode" if consistent results are required: Admin Console > Field Service > Scheduling Rules > Advanced > Deterministic Mode.

### Related

- Known Issues: KI-2402-003 (Same-location scheduling conflicts)
- Troubleshooting Guide: Error NT-3200

---

## KB-005: Post-Upgrade Performance Optimization

**Last Updated:** May 20, 2024  
**Applies To:** NovaTech Platform v24.2, v24.2.1  
**Category:** Platform / Performance

### Overview

After upgrading to NovaTech Platform v24.2 (or applying the v24.2.1 hotfix), some customers experience performance degradation. This article provides a systematic approach to diagnosing and resolving post-upgrade performance issues.

> ⚠️ **Important:** Performance degradation after applying the v24.2.1 hotfix is a known issue (KI-2402-006) under active investigation. Follow the steps below, but if issues persist, the cause may be **environment-specific** and require NovaTech Support investigation with diagnostic logs.

### Step 1 — Check Index Rebuild Status

The v24.2.1 hotfix triggers a database index rebuild that can take **4–6 hours** depending on your data volume. During this period, you will experience degraded performance. This is expected.

**To check:**
1. Open Admin Console > System > Background Jobs
2. Look for job: `IndexRebuildJob_v2421`
3. Check status:
   - **Running:** Wait for completion. Do not restart services during the rebuild.
   - **Completed:** Index rebuild is done. If performance is still degraded, continue to Step 2.
   - **Failed:** Contact NovaTech Support. Do NOT manually re-trigger the job.

### Step 2 — Verify System Resources

After the index rebuild completes, check system resources:

```bash
novatech-cli system health-check --full
```

Key metrics to review:
- **CPU usage:** Should be below 70% during normal operations. If consistently above 85%, consider scaling up.
- **Memory usage:** Should be below 80% of allocated memory. If above, check for memory leaks (see Step 3).
- **Disk I/O:** Check for I/O bottlenecks, especially on the database volume.
- **Database connections:** Should be below 80% of the connection pool maximum.

### Step 3 — Check for Known Memory Leak (v24.2)

NovaTech Platform v24.2 had a known memory leak in the asset tracking sync service. This was fixed in v24.2.1, but the fix changed garbage collection behavior which may cause more frequent GC pauses under high load.

**To check:**
```bash
novatech-cli service memory-trend --service sync-service --period 24h
```

If memory usage shows a continuous upward trend (even after v24.2.1), restart the sync service:
```bash
novatech-cli service restart --service sync-service
```

### Step 4 — Optimize Report Cache

The new report caching layer in v24.2 can significantly improve performance, but needs proper configuration:

1. Check cache hit rate: Admin Console > System > Cache Statistics
2. If hit rate is below 50%, the default cache configuration may not suit your usage patterns
3. Recommended cache settings for large deployments:
   - `cache.maxSize`: 2GB (default: 512MB)
   - `cache.ttl.reports`: 30 minutes (default: 60 minutes — lower TTL reduces stale data risk)
   - `cache.ttl.queries`: 5 minutes (default: 15 minutes)
   - `cache.evictionPolicy`: LRU (default)

### Step 5 — Review Background Job Concurrency

If too many background jobs run simultaneously, they can starve normal operations of resources.

1. Open Admin Console > System > Background Jobs > Concurrency Settings
2. Recommended settings after upgrade:
   - Max concurrent report generation jobs: 3 (default: 5)
   - Max concurrent sync jobs: 5 (default: 10)
   - Max concurrent import jobs: 2 (default: 3)
3. Gradually increase concurrency as system stabilizes

### Step 6 — Database Statistics Update

After the index rebuild, database query plans may be suboptimal because table statistics are stale.

```bash
novatech-cli db update-statistics --mode full
```

This takes 30-60 minutes for large databases and should be run during off-peak hours.

### Step 7 — Collect Diagnostics

If performance issues persist after following steps 1-6, collect diagnostic information and contact NovaTech Support:

```bash
novatech-cli diagnostics collect --include memory,db,services,jobs,cache --period 24h --output diagnostics.zip
```

Include in your support ticket:
- The diagnostics.zip file
- A description of specific performance symptoms (which modules/operations are slow)
- When the performance degradation started (after upgrade, after hotfix, gradually)
- Your environment details (infrastructure, user count, data volume)

> **Important:** If you've followed all the steps above and performance is still degraded, the root cause is likely **environment-specific** and related to your particular data distribution, usage patterns, or infrastructure configuration. NovaTech Support will need the diagnostics data to investigate further. This is an area of active investigation (KI-2402-006) and NovaTech engineers are working on a more comprehensive fix for v24.2.2.

### Related

- Known Issues: KI-2402-006 (System-wide performance degradation)
- Troubleshooting Guide: General Performance Troubleshooting
- Troubleshooting Guide: Error NT-6001 (Memory Threshold Exceeded)
- KB-008: Database Performance Tuning

---

## KB-006: Single Sign-On Configuration Guide

**Last Updated:** March 5, 2024  
**Applies To:** NovaTech Platform v24.1, v24.2  
**Category:** Security / Authentication

### Overview

NovaTech Platform supports Single Sign-On (SSO) using SAML 2.0 protocol with major identity providers including Microsoft Azure AD, Okta, OneLogin, and PingFederate.

### Supported Identity Providers

| Provider | Protocol | Status |
|---|---|---|
| Microsoft Azure AD | SAML 2.0 | Fully Supported |
| Okta | SAML 2.0 | Fully Supported |
| OneLogin | SAML 2.0 | Fully Supported |
| PingFederate | SAML 2.0 | Fully Supported |
| Google Workspace | SAML 2.0 | Community Supported |
| Custom SAML 2.0 | SAML 2.0 | Supported (manual configuration) |

### Configuration Steps (Azure AD Example)

1. In Azure AD, create a new Enterprise Application
2. Select "Non-gallery application"
3. Configure SAML SSO:
   - Identifier (Entity ID): `https://your-instance.novatech.com/saml/metadata`
   - Reply URL (ACS): `https://your-instance.novatech.com/saml/acs`
   - Sign-on URL: `https://your-instance.novatech.com/saml/login`
4. Download the Federation Metadata XML from Azure AD
5. In NovaTech Admin Console > Security > SSO Configuration:
   - Upload the Federation Metadata XML
   - Configure user attribute mapping (email, first name, last name, department)
   - Configure group-to-role mapping
   - Enable SSO

### Attribute Mapping

| NovaTech Field | SAML Attribute | Required |
|---|---|---|
| Email | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress` | Yes |
| First Name | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/givenname` | Yes |
| Last Name | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/surname` | Yes |
| Department | `http://schemas.xmlsoap.org/ws/2005/05/identity/claims/department` | No |
| Employee ID | Custom attribute | No |

### Troubleshooting SSO

- **Error NT-2187 after SSO login:** The SAML token has expired. Check token lifetime settings in your identity provider. Recommended: 60 minutes for id_token.
- **Users can log in via SSO but have no permissions:** Check group-to-role mapping configuration. Users must be assigned to at least one group that maps to a NovaTech role.
- **SSO login page shows "Invalid SAML Response":** Verify that the clock on the NovaTech server is synchronized within 5 minutes of the identity provider server.

### Related

- Troubleshooting Guide: Error NT-2187 (Authentication Token Expired)

---

## KB-007: API Integration Best Practices

**Last Updated:** April 15, 2024  
**Applies To:** NovaTech Platform v24.1, v24.2  
**Category:** Platform / API

### Overview

NovaTech Platform exposes a comprehensive REST API for integrations with third-party systems. This article covers best practices for building reliable, performant API integrations.

### Authentication

All API calls require authentication using one of:

1. **API Key:** Suitable for server-to-server integrations. Generated in Admin Console > Settings > API Keys.
2. **OAuth 2.0:** Suitable for user-context integrations and mobile apps. Supports authorization code flow and PKCE (v24.2+).
3. **Service Account Token:** For automated processes and CI/CD pipelines. Long-lived tokens with configurable scope.

### Rate Limits

| Support Tier | Rate Limit | Burst Limit |
|---|---|---|
| Standard | 100 requests/minute | 20 requests/second |
| Premium | 500 requests/minute | 50 requests/second |

**Best practices for rate limiting:**
- Monitor the `X-RateLimit-Remaining` and `X-RateLimit-Reset` headers
- Implement exponential backoff for HTTP 429 responses
- Use webhooks instead of polling where possible
- Batch API calls where supported (e.g., bulk asset import)

### Pagination

All list endpoints use cursor-based pagination:

```
GET /api/v2/assets?cursor=abc123&limit=100
```

- Default page size: 50 items
- Maximum page size: 500 items
- Always use the `nextCursor` from the response for subsequent pages

### Error Handling

NovaTech API uses standard HTTP status codes:

| Code | Meaning | Action |
|---|---|---|
| 200 | Success | Process response |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Check request body/parameters |
| 401 | Unauthorized | Refresh authentication token |
| 403 | Forbidden | Check permissions |
| 404 | Not Found | Verify resource ID |
| 429 | Rate Limited | Back off and retry |
| 500 | Server Error | Retry with backoff, contact support if persistent |

### Webhook Integration

NovaTech supports webhooks for real-time event notifications:

- Configure webhooks at Admin Console > Settings > Webhooks
- Supported events: asset.created, asset.updated, workorder.created, workorder.completed, report.generated, sync.failed
- Webhook payloads include event type, timestamp, and resource data
- Implement webhook signature verification for security

### Related

- API Reference Documentation
- Troubleshooting Guide: Error NT-1050 (API Rate Limit Exceeded)

---

## KB-008: Database Performance Tuning

**Last Updated:** May 15, 2024  
**Applies To:** NovaTech Platform v24.1, v24.2  
**Category:** Platform / Database

### Overview

This article provides guidance on tuning database performance for NovaTech Platform, particularly useful after major upgrades or when experiencing performance degradation.

### Recommended Database Configuration

#### Connection Pool Settings

| Setting | Small (<100 users) | Medium (100–1000 users) | Large (1000+ users) |
|---|---|---|---|
| `maxPoolSize` | 50 | 100 | 300 |
| `minPoolSize` | 10 | 25 | 50 |
| `connectionTimeout` | 30s | 30s | 30s |
| `idleTimeout` | 300s | 300s | 600s |
| `maxLifetime` | 1800s | 1800s | 1800s |

#### Memory Allocation

| Setting | Small | Medium | Large |
|---|---|---|---|
| `memory.maxHeapSize` | 4 GB | 8 GB | 16 GB |
| `memory.maxDirectMemory` | 2 GB | 4 GB | 8 GB |
| `cache.maxSize` | 256 MB | 512 MB | 2 GB |

### Database Maintenance Tasks

**Daily:**
- Monitor slow query log: `novatech-cli db slow-queries --threshold 5s --period 24h`
- Check connection pool utilization: `novatech-cli db pool-status`

**Weekly:**
- Update table statistics: `novatech-cli db update-statistics --mode incremental`
- Review index fragmentation: `novatech-cli db index-health`

**After upgrades:**
- Full statistics update: `novatech-cli db update-statistics --mode full`
- Index rebuild validation: `novatech-cli db validate-indexes`
- Query plan cache flush: `novatech-cli db flush-plan-cache`

### Common Performance Issues After v24.2 Upgrade

1. **Slow report generation:** The new reporting engine uses different query patterns. Run `novatech-cli db update-statistics --mode full` to help the query optimizer.
2. **High I/O during index rebuild:** Expected during the v24.2.1 hotfix. Allow 4–6 hours for completion.
3. **Connection pool exhaustion:** The new real-time sync service uses more connections than the old batch sync. Increase `maxPoolSize` by 50% if experiencing NT-3011 errors.
4. **Lock contention on asset tables:** The new event-driven sync may cause more frequent row-level locks. If experiencing timeouts, enable `row_level_locking_optimistic` mode.

### Monitoring

NovaTech exposes Prometheus-compatible metrics at `/metrics`:

- `novatech_db_query_duration_seconds` — Query execution time histogram
- `novatech_db_connection_pool_active` — Active connections
- `novatech_db_connection_pool_idle` — Idle connections
- `novatech_db_slow_queries_total` — Count of queries exceeding threshold

### Related

- KB-005: Post-Upgrade Performance Optimization
- Troubleshooting Guide: Error NT-3011 (Database Connection Timeout)
- Troubleshooting Guide: Error NT-6001 (Memory Threshold Exceeded)

---

*For issues not covered in these articles, contact NovaTech Support at support@novatech.com or visit our [Support Portal](https://support.novatech.com).*
