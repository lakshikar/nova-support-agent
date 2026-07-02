# NovaTech Platform — Troubleshooting Guide

**Last Updated:** May 10, 2024  
**Applies To:** NovaTech Platform v24.1, v24.2, v24.2.1

---

## How to Use This Guide

This guide covers common error codes, their causes, and resolution steps. Error codes follow the format `NT-XXXX` where the first digit indicates the module:

- **NT-1xxx:** Platform / Infrastructure
- **NT-2xxx:** Authentication & Security
- **NT-3xxx:** Database & Connectivity
- **NT-4xxx:** Asset Lifecycle & Reporting
- **NT-5xxx:** Asset Tracking & Synchronization
- **NT-6xxx:** Performance & Resource Management

---

## NT-1050 — API Rate Limit Exceeded

| Field | Details |
|---|---|
| **Module** | Platform / API Gateway |
| **Severity** | Medium |
| **Affected Versions** | All versions |
| **Symptoms** | API calls return HTTP 429 (Too Many Requests). Client applications display "Service temporarily unavailable" messages. |

### Cause

The tenant has exceeded the configured API rate limit. Default limits are:

- **Standard tier:** 100 requests/minute per API key
- **Premium tier:** 500 requests/minute per API key

Rate limits are enforced at the API gateway level per tenant, not per user.

### Resolution Steps

1. Check the `X-RateLimit-Remaining` response header to verify current usage.
2. Review API call patterns for unnecessary polling or retry loops.
3. Implement exponential backoff in client applications.
4. If legitimate traffic exceeds limits, request a rate limit increase through the Admin Console > Settings > API Limits.
5. Consider using webhooks instead of polling for event-driven integrations.

### Related KB Articles

- KB-007: API Integration Best Practices

---

## NT-2187 — Authentication Token Expired

| Field | Details |
|---|---|
| **Module** | Authentication & Security |
| **Severity** | Low |
| **Affected Versions** | All versions |
| **Symptoms** | Users are unexpectedly logged out. API calls return HTTP 401 (Unauthorized). Mobile app shows "Session expired, please log in again." |

### Cause

The user's authentication token has expired. Token lifetime is configurable:

- **Default:** 60 minutes (id_token), 8 hours (refresh_token)
- **SSO:** Token lifetime is controlled by the identity provider

Common triggers:
- User inactivity exceeding token lifetime
- Clock skew between client and server (>5 minutes)
- Token revocation due to password change or admin action

### Resolution Steps

1. Verify the user can log in successfully with fresh credentials.
2. If using SSO, check the identity provider's token lifetime settings.
3. Check for clock skew: `novatech-cli system check-clock-sync`
4. Review the authentication audit log for token revocation events.
5. If the issue persists, regenerate the user's API key from Admin Console.

### Related KB Articles

- KB-006: Single Sign-On Configuration Guide

---

## NT-3011 — Database Connection Timeout

| Field | Details |
|---|---|
| **Module** | Database & Connectivity |
| **Severity** | High |
| **Affected Versions** | All versions |
| **Symptoms** | Operations hang and eventually fail with timeout error. Admin Console shows database health as "Degraded." Log files show `ConnectionTimeoutException` with error code NT-3011. |

### Cause

The application server cannot establish a connection to the database within the configured timeout period (default: 30 seconds). Common causes:

- Database server overload (CPU >90% or memory >95%)
- Network connectivity issues between app server and database
- Connection pool exhaustion (all connections in use)
- Long-running queries blocking connection availability
- **After v24.2 upgrade:** Index rebuild process may temporarily degrade database performance (see KI-2402-006)

### Resolution Steps

1. Check database server health: CPU, memory, disk I/O, active connections.
2. Review the slow query log for long-running queries: `novatech-cli db slow-queries --threshold 10s`
3. Check connection pool status: `novatech-cli db pool-status`
4. If connection pool is exhausted, increase `maxPoolSize` in `database.config` (default: 100, recommended max: 500).
5. Check for index rebuild jobs in progress (relevant after v24.2/v24.2.1 upgrade): Admin Console > System > Background Jobs.
6. If the issue is intermittent, enable connection pool diagnostics: `novatech-cli db pool-diagnostics --enable`
7. Restart the application server as a temporary measure: `novatech-cli service restart --all`

### Related KB Articles

- KB-008: Database Performance Tuning
- KB-005: Post-Upgrade Performance Optimization

---

## NT-3200 — Scheduling Constraint Violation

| Field | Details |
|---|---|
| **Module** | Field Service / Scheduling |
| **Severity** | Medium |
| **Affected Versions** | v24.2, v24.2.1 |
| **Symptoms** | Schedule optimization fails or produces incomplete schedules. Log files show `ConstraintViolationException` with error code NT-3200. Some work orders remain unassigned after optimization. |

### Cause

The scheduling algorithm cannot find a valid assignment that satisfies all constraints. Common causes:

- Conflicting mandatory constraints (e.g., required skill not available in the scheduling window)
- Insufficient technician capacity for the number of work orders
- Travel time constraints making sequential assignments infeasible
- **Known issue (KI-2402-003):** Same-location work orders within 30 minutes may produce conflicting assignments

### Resolution Steps

1. Review the constraint violation report: Admin Console > Field Service > Schedule > Diagnostics.
2. Identify which constraints are causing the violation.
3. Consider relaxing non-critical constraints (e.g., change "preferred technician" from mandatory to optional).
4. Check for same-location work orders scheduled within 30 minutes (known issue KI-2402-003).
5. If the issue persists, manually assign the affected work orders and re-run optimization.
6. Export the scheduling diagnostic logs and contact NovaTech Support for further analysis.

### Related KB Articles

- KB-004: Field Service Scheduling Configuration

---

## NT-4401 — Report Template Not Found

| Field | Details |
|---|---|
| **Module** | Asset Lifecycle / Reporting |
| **Severity** | Medium |
| **Affected Versions** | v24.2, v24.2.1 |
| **Symptoms** | Report generation fails with "Template not found" error. The report was working in v24.1 but fails after upgrading to v24.2. |

### Cause

The v24.2 reporting engine uses a new report template format. Reports created in v24.1 or earlier reference legacy templates that are not automatically migrated. This is different from error NT-4523, which is specifically related to depreciation schedule compatibility.

### Resolution Steps

1. Open Admin Console > Reports > Migration.
2. Run the report migration wizard — this will convert legacy templates to the new format.
3. Review migrated reports for correctness, especially those with custom calculated columns.
4. If specific reports fail migration, manually recreate them using the new Report Builder UI.
5. Legacy reports can still be generated using the legacy endpoint as a temporary workaround: `GET /api/v1/reports/{reportType}`

### Related KB Articles

- KB-003: Migrating Reports to v24.2 Format

---

## NT-4523 — Asset Depreciation Report Generation Failure

| Field | Details |
|---|---|
| **Module** | Asset Lifecycle / Reporting |
| **Severity** | High |
| **Affected Versions** | v24.2, v24.2.1 |
| **Symptoms** | Generating the quarterly asset depreciation report fails with error code NT-4523. The error occurs during report rendering, typically after 30-60 seconds of processing. The error message reads: `ReportGenerationException: Depreciation schedule format incompatible with reporting engine v2 (NT-4523)`. |

### Cause

The new reporting engine in v24.2 uses an updated internal data format for depreciation schedules. **Custom depreciation schedules created before v24.1** use a legacy format that is not fully compatible with the new engine. Specifically:

- The legacy format stores depreciation rates as annual percentages
- The new engine expects monthly rate arrays with period-specific adjustments
- When the engine encounters a legacy schedule, it attempts conversion but fails for schedules with:
  - Custom mid-year convention rules
  - Non-standard fiscal year periods
  - Manual adjustment entries

**This does NOT affect:**
- Standard depreciation schedules (straight-line, declining balance) created in v24.1 or later
- Custom schedules created in v24.2 using the new template system
- Reports other than the quarterly depreciation report

### Resolution Steps

1. **Immediate Workaround (Recommended):**
   - Use the legacy report endpoint to generate the depreciation report: `GET /api/v1/reports/depreciation?format=legacy`
   - This uses the old reporting engine which is still available but will be removed in v25.1.

2. **Permanent Fix:**
   - Open Admin Console > Asset Lifecycle > Depreciation Schedules.
   - Identify schedules created before v24.1 (look for the "Legacy" badge).
   - For each legacy schedule:
     a. Export the current schedule parameters.
     b. Create a new schedule using v24.2 templates with the same parameters.
     c. Assign the new schedule to affected assets.
     d. Archive the legacy schedule.
   - Re-run the depreciation report.

3. **Validation:**
   - After migration, compare the output of the legacy and new reports to ensure values match.
   - Small rounding differences (< $0.01 per asset) are expected due to the change from annual to monthly rate calculations.

### Important Notes

- A permanent platform fix is planned for **v24.3** (expected July 2024) that will add automatic legacy schedule conversion during report generation.
- Do NOT delete legacy schedules — archive them for audit purposes.
- If you have more than 50 legacy schedules, contact NovaTech Support for a bulk migration script.

### Related KB Articles

- KB-001: Understanding Asset Depreciation in NovaTech
- KB-003: Migrating Reports to v24.2 Format

---

## NT-5098 — Sync Conflict Exception

| Field | Details |
|---|---|
| **Module** | Asset Tracking & Synchronization |
| **Severity** | High |
| **Affected Versions** | v24.2, v24.2.1 |
| **Symptoms** | Asset data is inconsistent across modules. Sync health dashboard shows failed sync events. Log files show `SyncConflictException: circular dependency detected` with error code NT-5098. |

### Cause

The new event-driven sync architecture in v24.2 detects and prevents circular dependency chains in asset state changes. A circular dependency occurs when:

- Asset A references Asset B (e.g., parent-child relationship)
- Asset B references Asset C
- Asset C references Asset A (directly or indirectly)

When a state change on any of these assets triggers a sync, the sync service detects the circular chain and throws NT-5098 rather than entering an infinite sync loop.

**This is more common than expected** because:
- The old sync service processed changes sequentially and didn't detect circular dependencies
- The new real-time sync processes changes in parallel, revealing previously hidden circular references
- Assets referenced across 3+ modules (Asset Lifecycle + Field Service + Supply Chain) are more likely to trigger this issue

### Resolution Steps

1. Identify the circular dependency chain: `novatech-cli sync diagnose --asset-id {assetId}`
2. Review the dependency chain and determine which reference should be removed or changed.
3. If the circular dependency is legitimate (e.g., mutual spare-part relationship), configure the sync service to exclude one direction: Admin Console > Asset Tracking > Sync Rules > Exclusions.
4. Trigger a manual full sync to re-establish consistent state: Admin Console > Asset Tracking > Sync Management > Full Sync.
5. Monitor the sync health dashboard for 24 hours to confirm resolution.

### Related KB Articles

- KB-002: Understanding Asset Tracking Sync in v24.2

---

## NT-6001 — Memory Threshold Exceeded

| Field | Details |
|---|---|
| **Module** | Platform / Performance |
| **Severity** | Critical |
| **Affected Versions** | All versions |
| **Symptoms** | Application becomes unresponsive or very slow. Admin Console shows memory health as "Critical." Log files show `OutOfMemoryWarning` with error code NT-6001. Services may restart automatically. |

### Cause

One or more services have exceeded the configured memory threshold (default: 85% of allocated memory). Common causes:

- Large report generation consuming excessive memory
- Memory leak in background services (see v24.2.1 hotfix notes for known memory leak)
- Insufficient memory allocation for the workload
- Too many concurrent users or API requests
- Cache size exceeding allocated memory

### Resolution Steps

1. Check current memory usage per service: `novatech-cli system memory-report`
2. Identify the service consuming the most memory.
3. If the issue is report generation, check for reports running against very large datasets. Consider adding filters or pagination.
4. If this started after applying v24.2.1 hotfix, the index rebuild process may be temporarily consuming additional memory. Allow 4–6 hours for completion.
5. Increase memory allocation if available: update `memory.maxHeapSize` in service configuration.
6. Restart the affected service to reclaim memory: `novatech-cli service restart --service {serviceName}`
7. Enable memory diagnostics for ongoing monitoring: `novatech-cli system memory-diagnostics --enable`

### Related KB Articles

- KB-005: Post-Upgrade Performance Optimization
- KB-008: Database Performance Tuning

---

## General Performance Troubleshooting

If the system is experiencing general slowness without a specific error code, follow these steps:

### Step 1 — Identify the Scope

Determine if the performance issue is:
- **System-wide** (all modules, all users) → Likely infrastructure or database issue
- **Module-specific** (only one module affected) → Check module-specific known issues
- **User-specific** (only certain users affected) → Check user session, permissions, or data volume

### Step 2 — Check System Health

Run the system health check: `novatech-cli system health-check --full`

This will report on:
- Database connectivity and query performance
- Service health and memory usage
- Background job status
- Cache hit rates
- Index health

### Step 3 — Check for Known Issues

After upgrading to v24.2 or applying the v24.2.1 hotfix, performance degradation is a **known issue** (KI-2402-006). Check:
- Is the index rebuild process still running? (Admin Console > System > Background Jobs)
- Has the hotfix been applied during a maintenance window?
- Has sufficient time elapsed for index rebuild (4–6 hours)?

### Step 4 — Collect Diagnostics

If the issue persists, collect diagnostic information:
```bash
novatech-cli diagnostics collect --include memory,db,services,jobs --output diagnostics.zip
```

Contact NovaTech Support with the diagnostics file for further investigation.

### Step 5 — Temporary Mitigation

While waiting for resolution:
- Restart services during off-peak hours: `novatech-cli service restart --all`
- Reduce concurrent background jobs: Admin Console > System > Background Jobs > Concurrency Settings
- Temporarily disable non-critical services (e.g., report caching, predictive scheduling)

---

*For issues not covered in this guide, contact NovaTech Support at support@novatech.com or visit our [Support Portal](https://support.novatech.com).*
