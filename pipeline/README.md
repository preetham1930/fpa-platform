# High-Volume Event Pipeline (Phase 4)

This directory contains the data generation and ingestion foundation for the Phase 4 streaming pipeline (Pub/Sub -> Dataflow -> BigQuery).

## Phase 4a: Event Generator

The `publish_transactions.py` script acts as a high-volume load generator. It creates synthetic, randomized financial transaction events that mirror the 6 valid line items in the FP&A platform model, and publishes them in high-throughput async batches directly to Google Cloud Pub/Sub.

### Event Schema
```json
{
  "transaction_id": "uuid-string",
  "department": "Engineering | HR | Marketing | Sales",
  "account": "Salaries | Ad Spend | Software Subscriptions",
  "amount": 1234.56,
  "event_timestamp": "2026-06-17T00:00:00.000000+00:00"
}
```

### Setup
Ensure you are authenticated against the target Google Cloud project (e.g. via `gcloud auth application-default login`).
```bash
# Install the publisher dependencies
pip install -r pipeline/requirements.txt
```

### Usage
```bash
python pipeline/publish_transactions.py --count 10000 --project fpa-platform --topic transactions
```

### Ground-Truth Aggregations
To mathematically verify the end-to-end pipeline in BigQuery (Phase 4c), this script maintains an internal running tally of the total amount and count of events for every `(department, account)` permutation. When the script completes publishing, it prints these ground-truth aggregates to the terminal. You should cross-reference these terminal numbers directly against your BigQuery windowed sums to guarantee no data loss and perfect at-least-once (or exactly-once) windowing semantics.
