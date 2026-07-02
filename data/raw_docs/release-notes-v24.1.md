# NovaTech Platform — Release Notes v24.1

**Release Date:** January 15, 2024  
**Release Type:** Major Release  
**Upgrade Path:** v23.4 → v24.1 (direct upgrade supported)

---

## Overview

NovaTech Platform v24.1 delivers significant enhancements across Asset Lifecycle Management, Field Service Operations, and Supply Chain modules. This release focuses on platform stability, reporting performance, and user experience improvements.

---

## Asset Lifecycle Module

### New Features

- **Bulk Asset Import Tool:** Administrators can now import up to 50,000 assets in a single batch operation via CSV upload. The import supports custom field mapping, validation rules, and duplicate detection.
- **Asset Dependency Mapping:** A new visual dependency graph shows parent-child relationships between assets, including shared maintenance schedules and spare part pools.
- **Depreciation Schedule Templates:** Pre-built templates for straight-line, declining balance, and sum-of-years depreciation methods. Templates can be customized per asset category.

### Improvements

- Asset search now supports wildcard patterns and partial matching across all custom fields.
- Asset history timeline has been redesigned with a new chronological view showing maintenance events, transfers, and valuation changes.
- Improved CSV export performance for large asset registries (10x faster for registries with >100,000 assets).

### Bug Fixes

- Fixed an issue where asset disposal records were not reflected in the quarterly depreciation report (previously showed disposed assets as active).
- Fixed a rare race condition in concurrent asset transfers that could result in duplicate ownership records.
- Resolved an issue where custom asset fields with special characters caused report generation to hang.

---

## Field Service Module

### New Features

- **Predictive Scheduling Suggestions:** The scheduling engine now offers AI-powered suggestions for optimal technician assignment based on skills, proximity, and historical job duration. This feature is in **beta** and must be enabled in tenant settings.
- **Offline Mode for Mobile App:** Field technicians can now complete work orders, capture signatures, and upload photos while offline. Data syncs automatically when connectivity is restored.

### Improvements

- Reduced scheduling algorithm execution time by 40% for large workforces (>500 technicians).
- Added support for recurring work orders with customizable recurrence patterns.
- Map view now shows real-time technician locations with 30-second refresh intervals.

### Bug Fixes

- Fixed GPS tracking drift on Android devices running OS 13+.
- Resolved an issue where cancelled work orders still appeared in the technician's daily schedule.
- Fixed a timezone handling bug that caused incorrect SLA deadline calculations for customers in UTC+offset zones greater than UTC+10.

---

## Supply Chain Module

### New Features

- **Supplier Scorecard Dashboard:** A new dashboard showing supplier performance metrics including on-time delivery rate, defect rate, and cost variance.
- **Automated Reorder Points:** The system can now automatically calculate and update reorder points based on historical consumption patterns and lead times.

### Improvements

- Purchase order approval workflow now supports up to 5 approval levels (previously limited to 3).
- Inventory valuation reports now support FIFO, LIFO, and weighted average costing methods.

### Bug Fixes

- Fixed an issue where partial shipment receipts were not correctly updating available inventory counts.
- Resolved a rounding error in multi-currency purchase orders that could result in penny discrepancies.

---

## Platform & Infrastructure

### Improvements

- Upgraded to .NET 8.0 runtime across all backend services.
- Database query optimizer improvements reducing average API response times by 15%.
- Enhanced audit logging now captures field-level change history for all core entities.
- New tenant-level rate limiting to prevent noisy-neighbor issues in multi-tenant deployments.

### Security

- Added support for SAML 2.0 Single Sign-On with Azure AD and Okta.
- Implemented row-level security for all report exports.
- Patched CVE-2024-0012 (low severity, no known exploits).

---

## API Changes

### New Endpoints

- `POST /api/v2/assets/bulk-import` — Bulk asset import
- `GET /api/v2/assets/{id}/dependencies` — Asset dependency graph
- `GET /api/v2/field-service/schedule/suggestions` — Predictive scheduling (beta)

### Deprecated Endpoints (will be removed in v25.1)

- `GET /api/v1/assets/search` — Use `GET /api/v2/assets/search` instead
- `POST /api/v1/work-orders/assign` — Use `POST /api/v2/work-orders/assign` instead

---

## Known Issues at Release

- **KI-2401-001:** Predictive scheduling suggestions may produce suboptimal results for workforces with fewer than 10 technicians. Fix planned for v24.2.
- **KI-2401-002:** Asset dependency graph does not render correctly in Safari 16.x. Workaround: use Chrome or Edge.
- **KI-2401-003:** Offline mode sync may fail silently if the work order was modified by another user while offline. A conflict resolution dialog will be added in v24.2.

---

## Upgrade Instructions

1. Review the [Pre-Upgrade Checklist](https://docs.novatech.com/upgrade/v24.1/checklist)
2. Back up your database and configuration files
3. Run the upgrade wizard from the Admin Console
4. Verify all custom integrations against the updated API
5. Test report generation for all custom reports

**Estimated Upgrade Time:** 2–4 hours (varies by data volume)

---

*For questions or issues related to this release, contact NovaTech Support at support@novatech.com or visit our [Support Portal](https://support.novatech.com).*
