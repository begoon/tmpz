import json
import requests

base = "http://metadata.google.internal/computeMetadata/v1"


def metadata() -> dict[str, str]:
    result = {}

    def recursive_get(root: str) -> None:
        url = f"{base}{root}"
        response = requests.get(url, headers={"Metadata-Flavor": "Google"})
        if response.status_code == 200:
            value = response.text.strip()
            if root.endswith("/"):
                for line in map(str.strip, value.splitlines()):
                    recursive_get(f"{root}{line}")
            else:
                value_ = value if len(value) < 80 else f"{value[:80]}..."
                print(f"{root}", "=", value_)
                result[root] = value

    recursive_get("/")
    return result


if __name__ == "__main__":
    print(json.dumps(metadata(), indent=2))
