# NovaTech Platform — Release Notes v24.2

**Release Date:** April 22, 2024  
**Release Type:** Major Release  
**Upgrade Path:** v24.1 → v24.2 (direct upgrade supported)

---

## Overview

NovaTech Platform v24.2 introduces a major overhaul of the Asset Lifecycle reporting engine, a redesigned Field Service scheduling algorithm, improvements to asset tracking synchronization, and significant platform scalability enhancements. This release also includes over 40 bug fixes and performance improvements.

---

## ⚠️ Important: Post-Release Hotfix v24.2.1

**Hotfix v24.2.1** was released on **May 18, 2024** to address critical indexing and caching issues introduced in v24.2. 

### What Changed in v24.2.1

- **Database Index Rebuild:** The v24.2 upgrade introduced new composite indexes on the `asset_transactions`, `work_order_events`, and `report_cache` tables. In some environments, these indexes were not built optimally during the upgrade, leading to **degraded query performance across all modules**. The hotfix forces a complete index rebuild.
- **Report Cache Invalidation Fix:** The new report caching layer (introduced in v24.2 — see below) had a bug where stale cached reports were served after data changes. The hotfix implements proper cache invalidation.
- **Memory Leak in Background Sync Service:** The asset tracking sync service (v24.2) had a memory leak that caused gradual performance degradation over 3–5 days of continuous operation. The hotfix adds proper resource disposal.
- **Dashboard Widget Rendering:** A CSS regression in v24.2 caused dashboard widgets to re-render excessively, increasing browser CPU usage by up to 300%. The hotfix optimizes the rendering pipeline.

> **⚠️ Known Issue with v24.2.1 Hotfix:** Some customers have reported **system-wide performance degradation** after applying the v24.2.1 hotfix, particularly affecting report generation, field service mobile app responsiveness, and dashboard loading times. This appears to be related to the index rebuild process running during peak hours. **Recommendation:** Apply the hotfix during a maintenance window and allow 4–6 hours for index rebuild to complete. If performance issues persist after 24 hours, contact NovaTech Support with diagnostic logs. Investigation is ongoing — see Known Issues KI-2402-006.

---

## Asset Lifecycle Module

### Major Change: New Reporting Engine

The Asset Lifecycle reporting engine has been **completely rewritten** in v24.2 to support:

- Real-time report generation (previously batch-only)
- Custom calculated columns using NovaTech Expression Language (NEL)
- Multi-format export (PDF, Excel, CSV, JSON)
- Report scheduling and automated distribution

**⚠️ Breaking Change:** Reports created in v24.1 and earlier use the legacy report format. These reports will continue to work but must be migrated to the new format by v25.1. A migration wizard is available in Admin Console > Reports > Migration.

**⚠️ Known Issue (NT-4523):** The new reporting engine has a known compatibility issue with the **quarterly asset depreciation report** when using custom depreciation schedules created before v24.1. The report generation fails with error code **NT-4523**. See Known Issues section for workaround. A permanent fix is planned for v24.3.

### New Features

- **Report Builder UI:** A drag-and-drop report builder for creating custom asset reports without SQL knowledge.
- **Depreciation Forecast:** New projection tool that forecasts asset depreciation over 1, 3, 5, or 10-year horizons.
- **Asset Health Score:** An AI-powered composite score (0–100) based on age, maintenance history, failure rate, and utilization.

### Improvements

- Asset register now supports up to 500,000 assets per tenant (previously 200,000).
- Improved asset search with natural language query support (beta).
- Bulk operations now show real-time progress with estimated completion time.

---

## Field Service Module

### Major Change: Redesigned Scheduling Algorithm

The Field Service scheduling algorithm has been **redesigned from the ground up** in v24.2:

- New constraint-based optimization engine replacing the previous heuristic approach.
- Support for complex scheduling constraints: skills, certifications, travel time, customer preferences, part availability.
- **Predictive scheduling** (beta in v24.1) is now **generally available** with improved accuracy.

**⚠️ Migration Note:** Existing scheduling rules from v24.1 are automatically migrated, but we recommend reviewing and re-testing all scheduling rules after upgrade. The new algorithm may produce different (generally better) schedules for the same inputs.

**⚠️ Known Issue:** In rare cases, the new scheduling algorithm may produce **conflicting assignments** when two work orders for the same customer location are scheduled within 30 minutes of each other. The algorithm fails to account for travel time between jobs at the same location with different entry points. This is tracked as KI-2402-003 and is being investigated.

### New Features

- **Dynamic Rescheduling:** The system can automatically reschedule affected work orders when a technician calls in sick or a job runs over time.
- **Customer Self-Service Scheduling:** End customers can select preferred time windows through a customer portal widget.
- **Parts Reservation:** Work orders can now reserve required parts from inventory, reducing "truck roll" cancellations due to missing parts.

### Improvements

- Mobile app now supports barcode and QR code scanning for asset identification.
- Work order forms support conditional logic (show/hide fields based on job type).
- Improved route optimization reducing average travel time by 18%.

---

## Asset Tracking & Synchronization

### Major Change: New Sync Architecture

The asset tracking synchronization service has been rebuilt on an **event-driven architecture**:

- Real-time sync between Asset Lifecycle, Field Service, and Supply Chain modules
- Event sourcing for complete audit trail of all asset state changes
- Support for offline-capable edge devices with conflict resolution

**⚠️ Known Issue:** The new sync service has intermittent **sync failures** for assets that are referenced across more than three modules simultaneously. The service logs show `SyncConflictException: circular dependency detected` errors. This is tracked as KI-2402-004 and is being actively investigated. **Workaround:** Manually trigger a full sync from Admin Console > Asset Tracking > Sync Management.

### Improvements

- Sync latency reduced from up to 15 minutes (v24.1) to near real-time (<30 seconds).
- Added sync health dashboard showing real-time sync status across all modules.
- Conflict resolution now supports three strategies: last-write-wins, source-priority, and manual review.

---

## Supply Chain Module

### New Features

- **AI-Powered Demand Forecasting:** Uses historical consumption, seasonality, and external factors to predict future demand for spare parts and consumables.
- **Supplier Integration Hub:** Direct EDI/API integration with major suppliers for automated PO submission and shipment tracking.

### Improvements

- Warehouse management now supports zone-based picking strategies.
- Improved lot tracking with full chain-of-custody visualization.

---

## Platform & Infrastructure

### Performance

- New **report caching layer** reduces repeated report generation time by up to 80%. Cache TTL is configurable per report type.
- **Query execution planner** now supports parallel query execution for complex reports.
- Background job scheduler has been migrated to a distributed architecture supporting horizontal scaling.

### Security

- Added support for OAuth 2.0 PKCE flow for mobile applications.
- New API key rotation policy enforcement (90-day maximum lifetime, configurable).
- Enhanced data encryption: all PII fields are now encrypted at rest using AES-256.

### Infrastructure

- Added support for Kubernetes deployment with Helm charts.
- New health check endpoints for all services (compatible with K8s liveness/readiness probes).
- Prometheus metrics endpoints for all core services.

---

## API Changes

### New Endpoints

- `POST /api/v2/reports/generate` — On-demand report generation
- `GET /api/v2/reports/{id}/status` — Report generation status
- `POST /api/v2/field-service/schedule/optimize` — Trigger schedule optimization
- `GET /api/v2/assets/{id}/health-score` — Asset health score
- `POST /api/v2/assets/sync/trigger` — Manual sync trigger

### Breaking Changes

- `GET /api/v2/reports/depreciation` now requires `reportFormat` parameter (previously defaulted to legacy format).
- `POST /api/v2/work-orders/assign` request body schema has changed to support new scheduling constraints. See [Migration Guide](https://docs.novatech.com/upgrade/v24.2/api-migration).

---

## Known Issues

| ID | Module | Description | Severity | Status | Workaround |
|---|---|---|---|---|---|
| KI-2402-001 | Asset Lifecycle | Error NT-4523 when generating quarterly depreciation report with pre-v24.1 custom depreciation schedules | High | Open — Fix planned for v24.3 | Recreate the depreciation schedule using v24.2 templates, or use the legacy report endpoint (`/api/v1/reports/depreciation`) as a temporary workaround |
| KI-2402-002 | Platform | Report cache does not invalidate properly when underlying data changes (fixed in v24.2.1) | Medium | Resolved in v24.2.1 | Apply hotfix v24.2.1 |
| KI-2402-003 | Field Service | Scheduling algorithm may produce conflicting assignments for same-location work orders within 30 minutes | Medium | Investigating | Manually review schedules for same-location jobs |
| KI-2402-004 | Asset Tracking | Sync failures for assets referenced across 3+ modules simultaneously | High | Investigating | Manual full sync from Admin Console |
| KI-2402-005 | Asset Lifecycle | Report Builder custom calculated columns using nested functions may produce incorrect results | Low | Open — Fix planned for v24.3 | Avoid nesting more than 2 functions in calculated columns |
| KI-2402-006 | Platform | System-wide performance degradation after applying v24.2.1 hotfix | Critical | Investigating | Apply hotfix during maintenance window; allow 4–6 hours for index rebuild; contact support if issues persist after 24 hours |

---

## Upgrade Instructions

1. **Important:** Read the full release notes, especially the breaking changes and known issues sections.
2. Schedule a maintenance window of at least **4 hours** (6 hours recommended for environments with >100,000 assets).
3. Back up your database, configuration files, and custom reports.
4. Run the pre-upgrade validation tool: `novatech-cli upgrade --validate --target v24.2`
5. Execute the upgrade: `novatech-cli upgrade --target v24.2`
6. Apply hotfix v24.2.1 immediately after upgrade.
7. Monitor the index rebuild process (Admin Console > System > Background Jobs).
8. Verify all custom integrations against the updated API.
9. Migrate legacy reports using the migration wizard (recommended within 30 days).
10. Test all scheduling rules in the new scheduling engine.

**Estimated Upgrade Time:** 4–6 hours (varies by data volume and environment size)

---

*For questions or issues related to this release, contact NovaTech Support at support@novatech.com or visit our [Support Portal](https://support.novatech.com).*
