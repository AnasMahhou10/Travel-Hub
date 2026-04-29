import base64
import gzip
import json


def pack_json(data) -> str:
    raw = json.dumps(data).encode("utf-8")
    compressed = gzip.compress(raw)
    return base64.b64encode(compressed).decode("ascii")


def unpack_json(data: str):
    try:
        compressed = base64.b64decode(data.encode("ascii"))
        raw = gzip.decompress(compressed)
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return json.loads(data)