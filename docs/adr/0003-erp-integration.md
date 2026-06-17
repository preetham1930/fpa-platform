# ADR 0003: ERP Integration and Idempotent Actuals Ingestion

**Status:** Accepted

## Context
During the initial phases, actuals were seeded manually by script to stand up the core variance engine. In a real-world FP&A context, actuals are pulled directly from a system of record, such as an SAP General Ledger. To demonstrate realistic enterprise integration patterns without access to a live SAP environment, we needed a realistic, testable ingestion path that models common integration challenges: field mapping, unmapped records, type validation, and idempotent writes.

## Decision
We decided to implement the integration using the following strategies:
1. **Swappable Connector Interface:** We introduced an `ERPConnector` ABC and implemented a `MockSAPConnector`. This allows the pipeline logic to be developed realistically while keeping the underlying data source swappable.
2. **External Mapping Table:** We introduced an `ExternalMapping` model to reliably translate external identifiers (e.g., `cost_center -> department`, `gl_account -> account`).
3. **Idempotent Upserts:** Data ingestion performs an `UPSERT` keyed on the natural key (`department_id`, `account_id`, `period_id`). Rerunning a sync will update values in place rather than duplicating records.
4. **Partial-Success Validation:** Instead of aborting an entire run when an invalid or unmapped record is encountered, the sync gracefully handles the failure. It increments a rejected count, logs the specific record and reason, and proceeds to sync the clean records.
5. **Auditable Sync Log:** Every integration trigger is logged in the `SyncRun` table, which captures the status (`success`, `partial`, `failed`), timestamps, row counts, and an `error_detail` JSON array. This is directly exposed in the runs responses.
6. **Isolated Variance Engine:** The Phase 1 variance engine and schemas remain unchanged. Actuals simply arrive via the new path with a marked `source`.

## Consequences
- **Positive:** We established highly realistic integration patterns. Data-quality issues (like unmapped cost centers) are visible and actionable by finance users without requiring engineering intervention. The pipeline is safe to trigger repeatedly.
- **Trade-offs:** 
  - The use of a mock SAP means there is no live connection managing network latency or real OAuth flows.
  - The UPSERT implementation is currently application-level (query-then-write) rather than relying on an atomic DB `ON CONFLICT` clause. While this means it isn't strictly safe under aggressive concurrent synchronization triggers, it is perfectly fine for our single-manual-trigger constraints.
  - Syncing remains a manual trigger for now; a production environment would likely move this to a Cloud Scheduler or cron job.
