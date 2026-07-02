# NovaTech Platform — Known Issues Registry

**Last Updated:** May 22, 2024  
**Current Version:** v24.2.1

---

## How to Use This Registry

This registry tracks all known issues across NovaTech Platform releases. Issues are categorized by severity and status:

- **Status:** Open, Investigating, Fix Planned, Resolved
- **Severity:** Critical, High, Medium, Low

---

## Open Issues — v24.2 / v24.2.1

### KI-2402-001 — Error NT-4523: Depreciation Report Failure

| Field | Details |
|---|---|
| **Severity** | High |
| **Module** | Asset Lifecycle / Reporting |
| **Affected Versions** | v24.2, v24.2.1 |
| **Status** | Open — Fix planned for v24.3 (ETA: July 2024) |
| **Reported By** | Multiple customers |
| **Date Reported** | April 28, 2024 |

**Description:**  
The quarterly asset depreciation report fails with error NT-4523 when using custom depreciation schedules created before v24.1. The new reporting engine in v24.2 cannot process legacy depreciation schedule formats.

**Impact:**  
Customers with legacy custom depreciation schedules cannot generate quarterly depreciation reports using the new reporting engine.

**Workaround:**  
1. Use the legacy report endpoint: `GET /api/v1/reports/depreciation?format=legacy`
2. Alternatively, recreate depreciation schedules using v24.2 templates (see Troubleshooting Guide, NT-4523)

**Root Cause:**  
The new reporting engine expects monthly rate arrays; legacy schedules store annual percentages with different mid-year convention formats.

**Fix Plan:**  
v24.3 will include automatic legacy schedule conversion during report generation.

---

### KI-2402-003 — Scheduling Conflicts for Same-Location Work Orders

| Field | Details |
|---|---|
| **Severity** | Medium |
| **Module** | Field Service / Scheduling |
| **Affected Versions** | v24.2, v24.2.1 |
| **Status** | Investigating |
| **Reported By** | Atlas Manufacturing, Pinnacle Energy, 3 others |
| **Date Reported** | May 3, 2024 |

**Description:**  
The redesigned scheduling algorithm in v24.2 may produce conflicting assignments when two or more work orders for the same customer location are scheduled within 30 minutes of each other. The algorithm does not account for different entry points or security check-in procedures at large industrial sites.

**Impact:**  
Technicians may receive conflicting schedules for jobs at the same location but different buildings/areas. This leads to missed appointments and SLA violations.

**Workaround:**  
- Manually review schedules for same-location work orders.
- Add a 30-minute buffer constraint between same-location jobs: Admin Console > Field Service > Scheduling Rules > Add Constraint > "Same Location Buffer."

**Investigation Notes (Internal):**  
- The root cause is that the constraint solver treats each work order independently and uses GPS coordinates for proximity detection. Two different buildings at a large industrial site (e.g., a factory complex) may have GPS coordinates within 50 meters but require 20+ minutes of travel between them.
- Engineering is exploring a "site zone" concept where customers can define zones within a location, each with their own travel-time estimates.

---

### KI-2402-004 — Asset Sync Failures Across 3+ Modules

| Field | Details |
|---|---|
| **Severity** | High |
| **Module** | Asset Tracking & Synchronization |
| **Affected Versions** | v24.2, v24.2.1 |
| **Status** | Investigating |
| **Reported By** | Multiple customers |
| **Date Reported** | May 5, 2024 |

**Description:**  
The new event-driven sync service intermittently fails for assets that are referenced across more than three modules simultaneously. The sync service detects circular dependency chains and throws `SyncConflictException` (NT-5098).

**Impact:**  
Asset data may become inconsistent across modules. For example, an asset's status may show as "Active" in Asset Lifecycle but "Decommissioned" in Field Service.

**Workaround:**  
- Trigger a manual full sync: Admin Console > Asset Tracking > Sync Management > Full Sync.
- Monitor the sync health dashboard for failed events.
- For frequently affected assets, configure sync exclusions to break the circular dependency.

**Investigation Notes (Internal):**  
- The v24.1 sequential sync service didn't detect circular dependencies — it just processed changes in order, which masked the underlying data model issue.
- The v24.2 parallel sync exposes these circular references because multiple sync events fire simultaneously.
- Engineering is considering a topological sort approach to detect and break cycles during sync planning rather than failing.
- Related to ticket TK-20251 (Atlas Manufacturing) where asset tracking sync failures were reported between Asset Lifecycle and Field Service modules.

---

### KI-2402-005 — Report Builder Nested Function Errors

| Field | Details |
|---|---|
| **Severity** | Low |
| **Module** | Asset Lifecycle / Reporting |
| **Affected Versions** | v24.2, v24.2.1 |
| **Status** | Open — Fix planned for v24.3 |
| **Reported By** | TerraCore Utilities, 1 other |
| **Date Reported** | May 8, 2024 |

**Description:**  
Custom calculated columns in the Report Builder may produce incorrect results when using more than 2 nested functions. For example, `ROUND(SUM(IF(...)))` may produce incorrect rounding.

**Impact:**  
Low — affects only customers using complex calculated columns in custom reports.

**Workaround:**  
Avoid nesting more than 2 functions. Break complex calculations into multiple columns.

---

### KI-2402-006 — System-Wide Performance Degradation After v24.2.1 Hotfix

| Field | Details |
|---|---|
| **Severity** | Critical |
| **Module** | Platform / Infrastructure |
| **Affected Versions** | v24.2.1 |
| **Status** | Investigating |
| **Reported By** | TerraCore Utilities, Meridian Energy, Global Dynamics Corp, 5 others |
| **Date Reported** | May 19, 2024 |

**Description:**  
Multiple customers have reported system-wide performance degradation after applying the v24.2.1 hotfix. Symptoms include:

- Report generation taking 3–5x longer than before the hotfix
- Field Service mobile app experiencing laggy responses and slow loading
- Dashboard widgets taking 10–30 seconds to render (previously 1–2 seconds)
- API response times increasing from ~200ms to 2–5 seconds
- Background job processing slowing significantly

**Impact:**  
Significant impact on daily operations for affected customers. Some customers have reported SLA breaches caused by system slowness preventing timely ticket resolution.

**Root Cause Analysis (In Progress):**  
The v24.2.1 hotfix includes a database index rebuild that is necessary to fix the caching issues from v24.2. However:

1. **Index rebuild timing:** The index rebuild runs as a background job that can take 4–6 hours for large databases. During this period, database performance is significantly degraded.
2. **Concurrent resource contention:** The rebuild job competes with normal operations for database I/O and CPU.
3. **Post-rebuild performance:** Some customers report that performance does NOT return to normal even after the index rebuild completes. Engineering is investigating whether the new index structure is suboptimal for certain query patterns.
4. **Memory pressure:** The memory leak fix in v24.2.1 changed the garbage collection behavior, which may be causing more frequent GC pauses under high load.

**Recommended Actions:**
1. Check if the index rebuild has completed: Admin Console > System > Background Jobs > Look for "IndexRebuildJob_v2421"
2. If the rebuild is still running, wait for completion before evaluating performance.
3. If the rebuild has completed and performance is still degraded:
   a. Collect diagnostics: `novatech-cli diagnostics collect --include memory,db,services,jobs --output diagnostics.zip`
   b. Contact NovaTech Support with the diagnostics file.
   c. As a temporary measure, restart all services during off-peak hours.
4. If performance is critical, NovaTech Support can assist with rolling back the index changes (note: this will re-introduce the caching bug from KI-2402-002).

**Next Steps:**  
- Engineering is preparing a targeted fix (v24.2.2) to optimize the new index structure. ETA: Late May / Early June 2024.
- A configuration guide for tuning index rebuild settings (batch size, concurrency) will be published this week.

---

## Resolved Issues

### KI-2402-002 — Report Cache Invalidation (RESOLVED)

| Field | Details |
|---|---|
| **Severity** | Medium |
| **Module** | Platform |
| **Affected Versions** | v24.2 |
| **Status** | ✅ Resolved in v24.2.1 |
| **Resolution Date** | May 18, 2024 |

**Description:**  
The new report caching layer served stale cached reports after underlying data changes. Users would see outdated report data until the cache TTL expired.

**Resolution:**  
Fixed in v24.2.1 hotfix. Proper cache invalidation now triggers when underlying data changes.

---

### KI-2401-001 — Predictive Scheduling Suboptimal for Small Workforces (RESOLVED)

| Field | Details |
|---|---|
| **Severity** | Medium |
| **Module** | Field Service / Scheduling |
| **Affected Versions** | v24.1 |
| **Status** | ✅ Resolved in v24.2 |
| **Resolution Date** | April 22, 2024 |

**Description:**  
Predictive scheduling feature (beta in v24.1) produced suboptimal assignment suggestions for organizations with fewer than 10 technicians.

**Resolution:**  
The scheduling algorithm was redesigned in v24.2 and now works effectively with any workforce size.

---

### KI-2401-002 — Asset Dependency Graph Safari Rendering (RESOLVED)

| Field | Details |
|---|---|
| **Severity** | Low |
| **Module** | Asset Lifecycle |
| **Affected Versions** | v24.1 |
| **Status** | ✅ Resolved in v24.2 |
| **Resolution Date** | April 22, 2024 |

**Description:**  
The asset dependency graph visualization did not render correctly in Safari 16.x.

**Resolution:**  
Fixed in v24.2 with updated frontend rendering library.

---

### KI-2401-003 — Offline Mode Sync Conflict (RESOLVED)

| Field | Details |
|---|---|
| **Severity** | Medium |
| **Module** | Field Service / Mobile |
| **Affected Versions** | v24.1 |
| **Status** | ✅ Resolved in v24.2 |
| **Resolution Date** | April 22, 2024 |

**Description:**  
Offline mode data sync would fail silently if the work order was modified by another user while the technician was offline.

**Resolution:**  
v24.2 adds a conflict resolution dialog that presents both versions to the user and allows manual merge.

---

## Reporting a New Issue

If you've discovered an issue not listed here:

1. Check the [Troubleshooting Guide](./troubleshooting-guide.md) first.
2. Search the [Knowledge Base](./knowledge-base-articles.md) for related articles.
3. If the issue is new, contact NovaTech Support:
   - **Premium customers:** support-premium@novatech.com (2-hour response SLA)
   - **Standard customers:** support@novatech.com (8-business-hour response SLA)
   - Include: error codes, steps to reproduce, diagnostic logs, and screenshots.

---

*This registry is updated weekly. For the latest information, visit [support.novatech.com/known-issues](https://support.novatech.com/known-issues).*
