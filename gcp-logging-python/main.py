import os
import sys
from datetime import datetime
from traceback import format_exception

import dotenv
import google.cloud.logging

dotenv.load_dotenv()


def log_struct(log_name, json_payload, project_id):
    client = google.cloud.logging.Client(project=project_id)
    logger = client.logger(log_name)
    logger.log_struct(json_payload)


def log_text(log_name, text, project_id):
    client = google.cloud.logging.Client(project=project_id)
    logger = client.logger(log_name)
    logger.log_text(text)


if __name__ == "__main__":
    try:
        try:
            raise Exception(datetime.now().isoformat())
        except Exception:
            raise ValueError("VALUE ERROR: " + datetime.now().isoformat())
    except Exception as e:
        project_id = os.getenv("PROJECT_ID")
        log_name = "logging-python"
        json_data = {
            "message": "PANIC: " + str(e),
            "stack_trace": "".join(format_exception(e)),
            "severity": "ERROR",
            "data": {
                "when": datetime.now().isoformat(),
                "verison": sys.version,
            },
        }
        log_struct(log_name, json_data, project_id)
