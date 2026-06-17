# Scale Report: Streaming Transaction Aggregation Pipeline

## Purpose

The Variance Platform's actuals normally arrive as periodic, pre-aggregated figures.
This pipeline demonstrates the platform handling **transaction-level financial events
at scale** — the raw, high-volume stream that real ERP and point-of-sale systems emit —
and continuously rolling them up into the same department/account aggregates the rest
of the platform consumes.

It exists to answer the question a reviewer would reasonably ask: *can this handle
web-scale volume, not just a seeded demo table?* The answer, measured below, is yes.

## Architecture

```
Cloud Pub/Sub        Apache Beam (Dataflow)          BigQuery
  topic        ──►   streaming aggregation    ──►    fpa_analytics.transaction_aggregates
"transactions"       (Pub/Sub → window → combine → BQ)
```

- **Ingestion — Cloud Pub/Sub.** A publisher (`publish_transactions.py`) emits synthetic
  transaction events (`{transaction_id, department, account, amount, event_timestamp}`)
  to the `transactions` topic. Pub/Sub is the durable, decoupled buffer between producers
  and the pipeline.
- **Processing — Apache Beam on Dataflow.** `aggregate_pipeline.py` reads the stream,
  windows it into fixed 60-second intervals, and computes a per-(department, account) sum
  and count per window.
- **Storage — BigQuery.** Each window's aggregates are appended to
  `fpa_analytics.transaction_aggregates`, a columnar warehouse table that scales
  independently of the operational Postgres database.

The same pipeline file runs unchanged on two runners — the **DirectRunner** for local
development and the **DataflowRunner** for production — selected at launch via `--runner`,
with no code branch.

## Pipeline design

**Event time = publish time.** `ReadFromPubSub` uses each message's Pub/Sub publish
timestamp as its event time. This is deliberate: windowing then depends on when events
actually entered the system, not on a payload field a producer could set incorrectly.

**Fixed 60-second windows.** `FixedWindows(60)` discretizes the unbounded stream into
non-overlapping one-minute buckets. Windowed results materialize when a window *closes* —
when the watermark passes the window's end — not when an event arrives.

**Distributable aggregation.** The sum and count are computed with a custom `CombineFn`
rather than a `GroupByKey` plus a manual reduce. A `CombineFn` is associative and
commutative, so Beam runs it in parallel across workers — partially aggregating on each
worker and merging the partial results — which is what lets the aggregation scale
horizontally. The job ran with a key parallelism of 1024.

**Window-stamped output.** A `DoFn` using `beam.DoFn.WindowParam` reads each result's
window boundaries and emits them as `window_start` / `window_end` TIMESTAMP fields, so
every BigQuery row is self-describing about the interval it summarizes.

**Append-only sink.** `WriteToBigQuery` uses `CREATE_IF_NEEDED` + `WRITE_APPEND` against
an explicit schema (department, account STRING; window_start/end TIMESTAMP; total_amount
FLOAT; event_count INTEGER).

## Verification

Correctness was proven by reconciliation: the publisher prints a ground-truth aggregate
table before sending, and the pipeline's BigQuery output must match it exactly.

- **Local (DirectRunner):** small bursts reconciled to the cent, confirming the
  parse → window → combine → write logic.
- **Production (Dataflow):** a **50,000-event** load reconciled **exactly** — all six
  (department, account) pairs matching the publisher's totals to the cent, with event
  counts summing to exactly 50,000. Zero loss.

| Department / Account | Events | Total (USD) |
|---|---|---|
| Engineering / Salaries | 8,287 | 20,988,930.29 |
| HR / Salaries | 8,406 | 21,175,795.62 |
| Marketing / Ad Spend | 8,283 | 20,952,570.33 |
| Marketing / Salaries | 8,389 | 21,181,685.85 |
| Sales / Salaries | 8,331 | 20,871,616.09 |
| Sales / Software Subscriptions | 8,304 | 41,595,902.99 |
| **Total** | **50,000** | **146,766,501.17** |

## Measured performance

- **Peak throughput:** ~724 elements/sec on a single `e2-standard-2` worker (Streaming Engine).
- **Extrapolated daily volume:** ~62 million events/day on one worker; with Dataflow
  autoscaling (capped at 2 workers here, unbounded in production), the architecture
  comfortably reaches tens of millions per day.
- **Key parallelism:** 1024 — the aggregation is partitioned by (department, account)
  across the worker pool.
- **Latency:** windowed results appear within seconds of a window closing; max
  per-operation latency under one second.

## Runner differences (a deliberate dev/prod split)

Developing locally and verifying in production exposed real, instructive differences:

- **DirectRunner (local):** advances its watermark on processing/wall-clock time. It does
  not advance the watermark on an idle stream, and it drops the tail of a large burst as
  late data (a 1,000-event local burst landed only ~6%). Excellent for validating *logic*
  cheaply; it cannot validate *volume*.
- **DataflowRunner (production):** advances the watermark from the oldest unacknowledged
  Pub/Sub message, so it never outruns the data — the full burst lands inside its window.
  This is why volume verification belongs on Dataflow, and why the 50k run reconciled
  cleanly where a local burst could not.

## Operational lessons

Documented because they are the difference between a pipeline that runs in a tutorial and
one that runs in a real project:

- **Worker IAM.** Dataflow workers run as a service account that, on a locked-down project,
  has no permissions by default. It was granted exactly `dataflow.worker`, `pubsub.editor`,
  `bigquery.dataEditor`, `bigquery.jobUser`, and `storage.objectAdmin` — least privilege,
  nothing broader.
- **Zonal capacity.** An initial launch failed with `ZONE_RESOURCE_POOL_EXHAUSTED` — a
  Compute Engine stockout in one zone. Resolved by pinning a different zone and using the
  more widely available (and cheaper) E2 machine family.
- **DoFn serialization.** A pipeline that passed locally failed on Dataflow with
  `NameError: name 'timezone' is not defined`. DoFns are serialized and shipped to remote
  workers, and module-level imports do not reliably travel with them. Fix: import
  dependencies *inside* the DoFn so each is self-contained (the alternative being
  `--save_main_session`).
- **Drain vs. cancel.** Draining a streaming job stops ingestion, fires all pending
  windows, and flushes buffered data to the sink before stopping — used here to shut the
  job down without losing in-flight results. Cancel stops immediately and drops in-flight
  data.

## Cost

At demo scale, Pub/Sub and BigQuery fall within their free tiers; Dataflow is the only
meaningful cost, and only while a streaming job is running. The job was therefore run as a
**bounded load test and then drained**, with a billing budget alert as a backstop — a
streaming job left running is the one real cost risk.

## Scaling and guarantees

- **Horizontal scale:** Dataflow autoscales the worker pool; the key-partitioned
  `CombineFn` distributes the aggregation; fixed windows bound the in-flight state.
- **Processing guarantee:** Dataflow provides exactly-once *processing*. BigQuery streaming
  inserts are at-least-once with best-effort de-duplication; a stricter end-to-end
  exactly-once sink (the BigQuery Storage Write API) would be the next step for a
  production deployment.
