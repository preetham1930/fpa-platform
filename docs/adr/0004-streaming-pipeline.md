# ADR-0004: Streaming Data Pipeline (Pub/Sub → Dataflow → BigQuery)

## Status

Accepted

## Context

Elsewhere the platform handles actuals as periodic, pre-aggregated figures. To
demonstrate the system at web scale, it needed to process **transaction-level
financial events** — the high-volume streams that real ERP and point-of-sale systems
emit — and roll them up continuously. The target was a pipeline credibly capable of
millions of events per day, built on Google Cloud, and verifiable for correctness rather
than asserted.

## Decision

Implement a streaming pipeline with three managed components:

- **Cloud Pub/Sub** as the durable ingestion buffer that decouples producers from the
  processor.
- **Apache Beam on Cloud Dataflow** for windowed aggregation.
- **BigQuery** as the analytical sink.

Key design choices:

- **Event time = Pub/Sub publish time**, so windowing reflects when events entered the
  system rather than a payload field a producer could set incorrectly.
- **Fixed 60-second windows** to discretize the unbounded stream into deterministic
  buckets.
- **A custom `CombineFn`** (associative and commutative) for the sum and count, so Beam
  can partially aggregate on each worker and merge — distributing the work horizontally.
- **One pipeline file, two runners:** the same code runs on the `DirectRunner` for local
  development and the `DataflowRunner` in production, selected at launch via `--runner`.
- **BigQuery is the endpoint** — a scalable warehouse for the aggregated actuals. Feeding
  results back into the operational Postgres database is deliberately out of scope for
  this phase.

## Alternatives considered

- **A lightweight Cloud Run consumer** pulling from Pub/Sub and aggregating in-process.
  Simpler and cheaper, but it would not demonstrate managed autoscaling, watermark-based
  windowing, or exactly-once processing — the properties that make the "millions of
  events per day" claim real — and would not scale horizontally the same way.
- **Design-only (no running pipeline).** Rejected: the goal was a *verified* capability,
  not a diagram. The pipeline was load-tested and reconciled to the cent.

## Consequences

- **Positive:** real horizontal autoscaling and exactly-once *processing* via Dataflow; a
  measured peak of ~724 events/sec on a single worker (~62M/day extrapolated); BigQuery
  scales independently of the operational database; correctness proven by reconciling a
  50,000-event load exactly against publisher ground truth.
- **Trade-offs:** Dataflow is the one meaningful cost — mitigated by running the pipeline
  as a bounded load test and then draining it, with a billing budget alert as a backstop.
  The managed-streaming path also surfaced real operational requirements (worker-service-
  account IAM, zonal capacity, and DoFn serialization on remote workers), which are
  documented so they are reproducible rather than incidental.

See the [Scale Report](../scale-report.md) for the full architecture, verification
results, measured performance, and operational lessons.
