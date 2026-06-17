import argparse
import json
import logging
from datetime import timezone

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions

class ParseEvent(beam.DoFn):
    def process(self, element):
        import json, logging
        try:
            event = json.loads(element.decode("utf-8"))
            yield ((event["department"], event["account"]), {"amount": event["amount"], "count": 1})
        except Exception as e:
            logging.error(f"Failed to parse event: {e}")

class CombineAggregates(beam.CombineFn):
    def create_accumulator(self):
        return {"amount": 0.0, "count": 0}

    def add_input(self, accumulator, input_element):
        accumulator["amount"] += input_element["amount"]
        accumulator["count"] += input_element["count"]
        return accumulator

    def merge_accumulators(self, accumulators):
        merged = {"amount": 0.0, "count": 0}
        for acc in accumulators:
            merged["amount"] += acc["amount"]
            merged["count"] += acc["count"]
        return merged

    def extract_output(self, accumulator):
        return accumulator

class FormatForBigQuery(beam.DoFn):
    def process(self, element, window=beam.DoFn.WindowParam):
        from datetime import timezone
        (department, account), aggregates = element
        
        # window.start and window.end are beam.utils.timestamp.Timestamp objects
        # We need to convert them to ISO strings for BigQuery TIMESTAMP fields
        window_start = window.start.to_utc_datetime().replace(tzinfo=timezone.utc).isoformat()
        window_end = window.end.to_utc_datetime().replace(tzinfo=timezone.utc).isoformat()
        
        yield {
            "department": department,
            "account": account,
            "window_start": window_start,
            "window_end": window_end,
            "total_amount": round(aggregates["amount"], 2),
            "event_count": aggregates["count"]
        }

def run(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_topic",
        required=True,
        help="Input PubSub topic of the form 'projects/<PROJECT>/topics/<TOPIC>'."
    )
    parser.add_argument(
        "--output_table",
        required=True,
        help="Output BigQuery table of the form '<PROJECT>:<DATASET>.<table>'."
    )
    
    known_args, pipeline_args = parser.parse_known_args(argv)

    options = PipelineOptions(pipeline_args)
    options.view_as(StandardOptions).streaming = True

    table_schema = {
        "fields": [
            {"name": "department", "type": "STRING", "mode": "REQUIRED"},
            {"name": "account", "type": "STRING", "mode": "REQUIRED"},
            {"name": "window_start", "type": "TIMESTAMP", "mode": "REQUIRED"},
            {"name": "window_end", "type": "TIMESTAMP", "mode": "REQUIRED"},
            {"name": "total_amount", "type": "FLOAT", "mode": "REQUIRED"},
            {"name": "event_count", "type": "INTEGER", "mode": "REQUIRED"},
        ]
    }

    with beam.Pipeline(options=options) as p:
        (
            p
            | "ReadFromPubSub" >> beam.io.ReadFromPubSub(topic=known_args.input_topic)
            | "ParseEvent" >> beam.ParDo(ParseEvent())
            | "WindowInto" >> beam.WindowInto(beam.window.FixedWindows(60))
            | "Aggregate" >> beam.CombinePerKey(CombineAggregates())
            | "FormatForBQ" >> beam.ParDo(FormatForBigQuery())
            | "WriteToBigQuery" >> beam.io.WriteToBigQuery(
                table=known_args.output_table,
                schema=table_schema,
                create_disposition=beam.io.BigQueryDisposition.CREATE_IF_NEEDED,
                write_disposition=beam.io.BigQueryDisposition.WRITE_APPEND
            )
        )

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.INFO)
    run()
