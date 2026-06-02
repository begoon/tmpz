import urllib.request

METADATA_BASE = "http://169.254.169.254/latest"


def main():
    token_req = urllib.request.Request(
        f"{METADATA_BASE}/api/token",
        method="PUT",
        headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
    )
    with urllib.request.urlopen(token_req, timeout=5) as resp:
        token = resp.read().decode()

    id_req = urllib.request.Request(
        f"{METADATA_BASE}/meta-data/instance-id",
        headers={"X-aws-ec2-metadata-token": token},
    )
    with urllib.request.urlopen(id_req, timeout=5) as resp:
        print(resp.read().decode())


if __name__ == "__main__":
    main()
