import random
from time import sleep

from opentelemetry import trace
from opentelemetry.context import attach, detach
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.propagate import extract
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
)

traceparent = hex(random.getrandbits(128))[2:]

carrier = {'traceparent': f'00-{traceparent}-0000000000000001-01'}
print("carrier", carrier)
token = attach(extract(carrier))

cloud_trace_exporter = CloudTraceSpanExporter()
tracer_provider = TracerProvider()
tracer_provider.add_span_processor(BatchSpanProcessor(cloud_trace_exporter))
if False:
    tracer_provider.add_span_processor(
        SimpleSpanProcessor(ConsoleSpanExporter())
    )
trace.set_tracer_provider(tracer_provider)

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("palms/enrollment/call") as s:
    print("trace_id", hex(s.get_span_context().trace_id))
    sleep(0.25)

    s.set_attribute("string_attribute", "str")
    s.set_attribute("bool_attribute", False)
    s.set_attribute("int_attribute", 3)
    s.set_attribute("float_attribute", 3.14)

    with tracer.start_as_current_span("palms/enrollment/call/nested") as s1:
        print("trace_id", hex(s1.get_span_context().trace_id))
        sleep(0.25)
        s1.add_event(name="pad/before", attributes={"before": "10"})
        with tracer.start_span("palms/enrollment/call/nested/nested-1") as s2:
            print("trace_id", hex(s2.get_span_context().trace_id))
            sleep(0.25)
        s1.add_event(name="pad/after", attributes={"after": "20"})

    s.add_event(name="pad/end", attributes={"end": "done"})
    sleep(0.25)

detach(token)

tracer_provider.shutdown()
