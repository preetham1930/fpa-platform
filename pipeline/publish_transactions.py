import argparse
import json
import uuid
import random
import datetime
from google.cloud import pubsub_v1
from collections import defaultdict

VALID_LINE_ITEMS = [
    ("Engineering", "Salaries", "cost"),
    ("HR", "Salaries", "cost"),
    ("Marketing", "Salaries", "cost"),
    ("Marketing", "Ad Spend", "cost"),
    ("Sales", "Salaries", "cost"),
    ("Sales", "Software Subscriptions", "revenue"),
]

def generate_event():
    dept, acc, acc_type = random.choice(VALID_LINE_ITEMS)
    if acc_type == "cost":
        amount = round(random.uniform(50.0, 5000.0), 2)
    else:
        amount = round(random.uniform(100.0, 10000.0), 2)
        
    return {
        "transaction_id": str(uuid.uuid4()),
        "department": dept,
        "account": acc,
        "amount": amount,
        "event_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10000, help="Number of events to generate")
    parser.add_argument("--project", type=str, default="fpa-platform", help="Google Cloud Project ID")
    parser.add_argument("--topic", type=str, default="transactions", help="Pub/Sub Topic name")
    args = parser.parse_args()

    # Initialize publisher with batching for high throughput
    batch_settings = pubsub_v1.types.BatchSettings(
        max_messages=1000,
        max_bytes=1024 * 1024,
        max_latency=0.05,
    )
    publisher = pubsub_v1.PublisherClient(batch_settings=batch_settings)
    topic_path = publisher.topic_path(args.project, args.topic)

    print(f"Publishing {args.count} events to {topic_path}...")

    totals = defaultdict(lambda: {"count": 0, "sum": 0.0})
    grand_total_count = 0
    grand_total_sum = 0.0

    futures = []

    for _ in range(args.count):
        event = generate_event()
        
        # Track ground truth
        key = (event["department"], event["account"])
        totals[key]["count"] += 1
        totals[key]["sum"] += event["amount"]
        grand_total_count += 1
        grand_total_sum += event["amount"]

        data_str = json.dumps(event)
        data = data_str.encode("utf-8")
        
        # Publish asynchronously
        future = publisher.publish(topic_path, data)
        futures.append(future)

    # Await all futures to ensure delivery
    for future in futures:
        future.result()

    print("\n--- GROUND TRUTH AGGREGATES ---")
    print(f"{'Department':<15} | {'Account':<25} | {'Count':<8} | {'Total Amount'}")
    print("-" * 70)
    
    for (dept, acc), metrics in sorted(totals.items()):
        print(f"{dept:<15} | {acc:<25} | {metrics['count']:<8} | ${metrics['sum']:,.2f}")
    
    print("-" * 70)
    print(f"{'GRAND TOTAL':<15} | {'':<25} | {grand_total_count:<8} | ${grand_total_sum:,.2f}")
    print("\nDone.")

if __name__ == "__main__":
    main()
