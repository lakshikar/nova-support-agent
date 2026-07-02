# NovaTech Platform — Service Level Agreement (SLA) Policy

**Effective Date:** January 1, 2024  
**Version:** 3.2  
**Last Reviewed:** March 15, 2024

---

## 1. Overview

This document defines the Service Level Agreement (SLA) commitments for NovaTech Platform support services. SLAs vary by **support tier** (Standard or Premium) and **issue severity** (Critical, High, Medium, Low).

---

## 2. Support Tiers

### 2.1 Standard Support

Included with all NovaTech Platform licenses.

| Feature | Details |
|---|---|
| **Support Hours** | Monday – Friday, 8:00 AM – 6:00 PM (customer's local timezone) |
| **Support Channels** | Email, Support Portal |
| **Account Manager** | Shared (pooled support team) |
| **Phone Support** | Not included |
| **Severity 1 After-Hours Support** | Not included |

### 2.2 Premium Support

Available as an add-on to any NovaTech Platform license.

| Feature | Details |
|---|---|
| **Support Hours** | Monday – Friday, 8:00 AM – 6:00 PM (customer's local timezone) |
| **24/7 Support** | Available for Severity 1 (Critical) issues only |
| **Support Channels** | Email, Support Portal, Phone, Dedicated Slack Channel |
| **Account Manager** | Dedicated named account manager |
| **Phone Support** | Included (direct line to senior support engineers) |
| **Severity 1 After-Hours Support** | Included — 24/7 on-call support engineer |

---

## 3. Severity Classification

Issues are classified by severity based on the following criteria:

### Severity 1 — Critical

- **Definition:** The NovaTech Platform is completely unavailable, or a core business function is non-operational, affecting all users. No workaround is available.
- **Examples:**
  - System-wide outage
  - Complete data loss or corruption
  - Security breach requiring immediate action
  - All users unable to log in

### Severity 2 — High

- **Definition:** A major feature or function is significantly impaired, affecting multiple users or a critical business process. A workaround may exist but is not sustainable long-term.
- **Examples:**
  - Report generation failing for a specific module (e.g., NT-4523)
  - Scheduling algorithm producing incorrect assignments
  - Data synchronization failures between modules
  - Performance degradation affecting daily operations

### Severity 3 — Medium

- **Definition:** A feature or function is partially impaired, but the impact is limited. A reasonable workaround is available.
- **Examples:**
  - A specific report exports incorrectly
  - UI rendering issues in a specific browser
  - Non-critical API endpoint returning errors
  - Slow performance for a specific operation (not system-wide)

### Severity 4 — Low

- **Definition:** A minor issue, cosmetic defect, or general question. No significant business impact.
- **Examples:**
  - Documentation error
  - Feature request or enhancement suggestion
  - Minor UI alignment issue
  - General "how-to" question

---

## 4. SLA Response and Resolution Times

### 4.1 Response Time SLA

Response time is measured from the moment NovaTech Support receives the ticket to the first meaningful response (acknowledgment with initial assessment, not an auto-reply).

| Severity | Standard Support | Premium Support |
|---|---|---|
| **Critical (Sev 1)** | 8 business hours | 2 business hours (24/7) |
| **High (Sev 2)** | 8 business hours | 4 business hours |
| **Medium (Sev 3)** | 2 business days | 8 business hours |
| **Low (Sev 4)** | 5 business days | 2 business days |

### 4.2 Resolution Time SLA

Resolution time is measured from ticket creation to confirmed resolution (issue fixed and verified by the customer).

| Severity | Standard Support | Premium Support |
|---|---|---|
| **Critical (Sev 1)** | 5 business days | 2 business days |
| **High (Sev 2)** | 10 business days | 5 business days |
| **Medium (Sev 3)** | 15 business days | 8 business days |
| **Low (Sev 4)** | 30 business days | 15 business days |

> **Note:** Resolution time SLA applies to providing a fix, workaround, or mitigation plan. For issues requiring a product release (e.g., bug fixes scheduled for the next version), the SLA is met when a workaround or mitigation is provided, not when the permanent fix is released.

### 4.3 Business Day and Business Hours Definition

- **Business Day:** Monday through Friday, excluding public holidays in the customer's registered country.
- **Business Hours:** 8:00 AM to 6:00 PM in the customer's local timezone (as registered in the NovaTech Support Portal).
- **One Business Day:** 10 business hours (8:00 AM to 6:00 PM).
- **Exception:** Premium Support Severity 1 issues are covered 24/7, including weekends and holidays.

---

## 5. Escalation Matrix

### 5.1 Automatic Escalation Triggers

| Trigger | Action |
|---|---|
| Response SLA breach | Escalate to Support Team Lead |
| 50% of resolution SLA elapsed with no progress | Escalate to Support Manager |
| 75% of resolution SLA elapsed with no resolution | Escalate to Director of Customer Support |
| Resolution SLA breach | Escalate to VP of Customer Success + notify Account Manager |
| Customer requests escalation | Immediate escalation to Support Manager |

### 5.2 Escalation Path

```
Level 1: Support Engineer (initial handler)
    ↓
Level 2: Senior Support Engineer (complex technical issues)
    ↓
Level 3: Support Team Lead (SLA at risk)
    ↓
Level 4: Support Manager (SLA breached or customer escalation)
    ↓
Level 5: Director of Customer Support (critical business impact)
    ↓
Level 6: VP of Customer Success (executive escalation)
```

### 5.3 Premium Support — Dedicated Escalation

Premium customers have additional escalation options:

- **Dedicated Account Manager:** Can escalate directly to Level 3+
- **Emergency Hotline:** Direct phone line to senior support engineers for Severity 1 issues
- **Executive Sponsor:** Named VP-level executive available for critical business escalations

---

## 6. SLA Breach Consequences and Service Credits

### 6.1 Service Credits

If NovaTech fails to meet the resolution time SLA, the customer is entitled to service credits:

| SLA Breach | Service Credit |
|---|---|
| Resolution time exceeded by up to 50% | 5% of monthly support fees |
| Resolution time exceeded by 50–100% | 10% of monthly support fees |
| Resolution time exceeded by more than 100% | 20% of monthly support fees |
| Multiple SLA breaches in a single quarter (3+) | 25% of quarterly support fees |

### 6.2 Credit Request Process

1. Customer submits a credit request through the Support Portal within 30 days of the SLA breach.
2. NovaTech reviews the request within 5 business days.
3. Approved credits are applied to the next billing cycle.

### 6.3 SLA Exclusions

SLA timers are **paused** in the following situations:

- **Awaiting Customer Response:** If NovaTech requests information from the customer, the SLA timer pauses until the customer responds. After 5 business days without a response, the ticket is set to "Pending Customer" status.
- **Third-Party Dependency:** If the issue requires action from a third-party vendor (e.g., cloud provider, identity provider), the SLA timer pauses for the third-party response period.
- **Scheduled Maintenance:** Issues arising during announced scheduled maintenance windows are not subject to SLA until the maintenance window ends.
- **Force Majeure:** Natural disasters, global infrastructure outages, or other events beyond NovaTech's reasonable control.

---

## 7. Ticket Lifecycle

### 7.1 Ticket Statuses

| Status | Description |
|---|---|
| **New** | Ticket created, awaiting initial triage |
| **Triaged** | Severity assessed, assigned to support engineer |
| **In Progress** | Active investigation and resolution underway |
| **Pending Customer** | Awaiting information or action from the customer |
| **Pending Engineering** | Escalated to engineering team (e.g., requires code fix) |
| **Resolved** | Solution provided, awaiting customer verification |
| **Closed** | Customer confirmed resolution, ticket closed |
| **Reopened** | Previously resolved ticket reopened due to recurrence |

### 7.2 Automatic Ticket Actions

- Tickets in "Pending Customer" for 10 business days are automatically closed with notification.
- Resolved tickets are automatically closed after 5 business days if the customer does not respond.
- Closed tickets can be reopened within 30 days if the issue recurs.

---

## 8. Supporting Multiple Tickets

When a customer has multiple open tickets, the following prioritization rules apply:

1. Tickets are prioritized by **severity** (Critical > High > Medium > Low).
2. Within the same severity, tickets are prioritized by **SLA deadline** (closest deadline first).
3. Customers can request re-prioritization through their Account Manager (Premium) or via the Support Portal (Standard).
4. **Related tickets:** If multiple tickets appear to be related to the same underlying issue, NovaTech may link them and track them under a single parent ticket. SLA applies to each ticket individually unless the customer agrees to consolidation.

---

## 9. Contact Information

| Support Tier | Contact Method | Details |
|---|---|---|
| **Standard** | Email | support@novatech.com |
| **Standard** | Support Portal | support.novatech.com |
| **Premium** | Email | support-premium@novatech.com |
| **Premium** | Phone | +1-800-NOVA-TECH (24/7 for Sev 1) |
| **Premium** | Slack | Dedicated channel (provisioned during onboarding) |
| **All** | Emergency | security@novatech.com (security incidents only) |

---

*This SLA policy is subject to the terms of your NovaTech Platform license agreement. For questions about your SLA coverage, contact your Account Manager or email sla@novatech.com.*
