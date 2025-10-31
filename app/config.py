from pydantic import BaseModel
from pathlib import Path
import json


class TLSConfig(BaseModel):
    country: str = "RU"
    state: str = "Moscow"
    locality: str = "Moscow"
    organization: str = "Demo Chat"
    common_name: str = "localhost"
    valid_days: int = 365
    key_bits: int = 2048


def load_tls_config(path: Path) -> TLSConfig:
    if not path.exists():
        return TLSConfig()
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return TLSConfig(**data)
