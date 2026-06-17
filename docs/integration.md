# ERP & SAP Integration Guide

The FP&A Variance Platform features a robust, enterprise-grade integration pipeline designed to ingest "actuals" from external systems of record.

## Data Flow

The ingestion pipeline follows a strict, step-by-step resolution flow:
1. **Source Extraction:** A connector extracts records from the external source (e.g., a mock SAP system).
2. **Validation:** Each record undergoes structural and type validation.
3. **Field Mapping:** External identifiers (e.g., cost centers, GL accounts) are mapped to internal platform database IDs via the `ExternalMapping` table.
4. **Idempotent Upsert:** Clean, mapped records are upserted into the `ActualLine` table, grouped by the natural key `(department_id, account_id, period_id)`.
5. **Variance Computation:** The Phase 1 variance engine automatically picks up the new actuals during its standard read paths without any required changes.

## The Mapping Model

External systems rarely share primary keys with internal reporting tools. To bridge this gap, the database utilizes an `ExternalMapping` model that contains:
- `source`: The string identifier of the external system (e.g., `"SAP"`).
- `entity_type`: The internal entity being mapped (e.g., `"department"`, `"account"`).
- `external_code`: The unique identifier in the external system (e.g., `"CC-1000"`).
- `internal_id`: The integer ID of the internal entity.

If a record arrives with an `external_code` that does not exist in the mapping table, it is safely rejected.

## Sync Logs & Partial Success

Real-world integrations are inherently noisy. Rather than aborting an entire batch due to a single invalid row, the integration pipeline uses a **partial-success** model. 

Every time a sync is triggered, a `SyncRun` record is created. It tracks:
- **Status:** `success` (all records mapped), `partial` (some records failed), or `failed` (catastrophic failure, like a missing period).
- **Counts:** `records_fetched`, `records_synced`, `records_rejected`.
- **Error Detail:** An auditable JSON string containing an array of rejected records and their specific failure reasons (e.g., `Unknown cost_center`). This detail is surfaced directly on the frontend Integrations tab for finance users to investigate and resolve.

## Triggering a Sync

A manual synchronization can be triggered via the UI's **Integration Hub**. Simply navigate to the "Integrations" tab and click **Sync from SAP**. The UI will block until the pipeline completes, then immediately fetch and display the run history.

## Swappability

Currently, the system uses a `MockSAPConnector` that generates deterministic, hardcoded records designed specifically to test the validation and mapping logic. 

Because the integration path sits behind an `ERPConnector` abstract base class, connecting to a real SAP instance, NetSuite, or any OData endpoint simply requires implementing a new child class with a concrete `fetch_actuals()` method. The validation, mapping, and upsert logic remains completely agnostic to the data source.
