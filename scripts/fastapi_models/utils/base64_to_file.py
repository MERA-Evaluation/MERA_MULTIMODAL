import os
import base64
import uuid


def save_base64_to_file(b64_str: str, output_dir: str = "/tmp") -> str:
    if not b64_str.startswith("data:"):
        raise ValueError("Expected data URI scheme (starting with 'data:')")

    header, encoded = b64_str.split(",", 1)
    parts = header.split(";")
    mime = parts[0][5:]
    if "/" not in mime:
        raise ValueError(f"Invalid mime type in data URI: {mime}")

    _, subtype = mime.split("/", 1)
    subtype_clean = subtype.split("+")[0].split(";")[0]
    ext = subtype_clean

    try:
        binary = base64.b64decode(encoded, validate=True)
    except Exception as e:
        raise ValueError("Base64 decode error: " + str(e))

    filename = f"{uuid.uuid4().hex}.{ext}"
    full_path = os.path.join(output_dir, filename)

    os.makedirs(output_dir, exist_ok=True)

    with open(full_path, "wb") as f:
        f.write(binary)

    return os.path.abspath(full_path)
