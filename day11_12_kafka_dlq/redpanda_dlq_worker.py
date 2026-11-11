import json
from datetime import datetime
from pydantic import BaseModel, ValidationError

class StreamEvent(BaseModel):
    event_id: str
    tenant: str
    metric_value: float

# Simulated stream batch from Redpanda/Kafka topic 'enterprise.events.raw'
RAW_KAFKA_MESSAGES = [
    b'{"event_id": "EVT-01", "tenant": "acme", "metric_value": 99.4}',
    b'{"event_id": "EVT-02", "tenant": "globex", "metric_value": "CORRUPT_FLOAT_STRING"}',
    b'MALFORMED_BINARY_GARBAGE_PAYLOAD',
    b'{"event_id": "EVT-03", "tenant": "acme", "metric_value": 42.1}'
]

VALID_SINK = []
DLQ_TOPIC_SINK = []

def process_message_with_dlq(raw_bytes: bytes, offset: int):
    try:
        decoded = json.loads(raw_bytes.decode("utf-8"))
        validated = StreamEvent(**decoded)
        VALID_SINK.append(validated.model_dump())
        print(f"✅ [Offset {offset}] Processed valid event: {validated.event_id}")
    except (UnicodeDecodeError, json.JSONDecodeError, ValidationError) as err:
        # Route poison pill to Dead Letter Queue with diagnostic metadata
        dlq_envelope = {
            "failed_offset": offset,
            "raw_payload": raw_bytes.decode("utf-8", errors="replace"),
            "error_type": type(err).__name__,
            "error_detail": str(err)[:160],
            "failed_at_utc": datetime.utcnow().isoformat()
        }
        DLQ_TOPIC_SINK.append(dlq_envelope)
        print(f"🚨 [Offset {offset}] Poison pill routed to DLQ ({type(err).__name__}) — Partition continues!")

if __name__ == "__main__":
    for idx, msg in enumerate(RAW_KAFKA_MESSAGES):
        process_message_with_dlq(msg, offset=idx)
    
    print(f"\n📊 Summary: {len(VALID_SINK)} valid events processed | {len(DLQ_TOPIC_SINK)} isolated in DLQ.")

# command line kafka docker testing 

#     # Start a local Redpanda broker
# docker run -d --name redpanda \
#   -p 9092:9092 -p 9644:9644 \
#   docker.redpanda.com/redpandadata/redpanda:latest \
#   redpanda start --mode dev-container --smp 1 --memory 1G \
#     --reserve-memory 0M --node-id 0 --check=false

# # Create the raw and dead-letter topics
# docker exec redpanda rpk topic create enterprise.events.raw
# docker exec redpanda rpk topic create enterprise.events.dlq

# # Produce a valid event and two poison-pill examples to the raw topic
# printf '%s\n' \
#   '{"event_id":"EVT-01","tenant":"acme","metric_value":99.4}' \
#   '{"event_id":"EVT-02","tenant":"globex","metric_value":"CORRUPT_FLOAT_STRING"}' \
#   'MALFORMED_BINARY_GARBAGE_PAYLOAD' \
#   | docker exec -i redpanda rpk topic produce enterprise.events.raw

# # Inspect the raw messages
# docker exec -it redpanda rpk topic consume enterprise.events.raw -o start

# # Inspect the DLQ (it stays empty until a Kafka-connected worker publishes failures)
# docker exec -it redpanda rpk topic consume enterprise.events.dlq -o start