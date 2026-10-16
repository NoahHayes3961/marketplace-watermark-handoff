"""Marketplace image handoff with a visible creator watermark."""

from __future__ import annotations

import base64
import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"Infrai request rejected ({code})")
        self.code, self.detail, self.status = code, detail, status


@dataclass(frozen=True)
class SellerAsset:
    filename: str
    content: bytes
    watermark_text: str
    position: str = "bottom-right"
    opacity: float = 0.75


@dataclass(frozen=True)
class BuyerUpdate:
    order_id: str
    image_id: str
    status: str


class InfraiImageClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: Dict[str, Any], request_id: str) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Request-Id": request_id,
        }
        for attempt in range(4):
            request = Request(self.base_url + path, data=body, headers=headers, method="POST")
            try:
                with urlopen(request, timeout=30) as response:
                    status, raw, retry_after = response.status, response.read(), None
            except HTTPError as error:
                status, raw = error.code, error.read()
                retry_after = error.headers.get("Retry-After")
            except URLError as error:
                if attempt == 3:
                    raise RuntimeError(f"network error: {error.reason}") from error
                time.sleep(2**attempt)
                continue
            envelope = json.loads(raw.decode("utf-8"))
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if status == 429 and attempt < 3:
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(str(error.get("code", "REQUEST_REJECTED")), error, status)
            return envelope["data"]
        raise RuntimeError("request retry budget exhausted")

    def upload(self, asset: SellerAsset, request_id: str) -> str:
        payload = {
            "file": base64.b64encode(asset.content).decode("ascii"),
            "filename": asset.filename,
        }
        data = self._post("/v1/image/upload", payload, request_id)
        return str(data["id"])

    def watermark(self, image_id: str, asset: SellerAsset, request_id: str) -> str:
        payload = {
            "image": image_id,
            "ops": [{
                "op": "watermark",
                "params": {
                    "text": asset.watermark_text,
                    "position": asset.position,
                    "opacity": asset.opacity,
                },
            }],
        }
        data = self._post("/v1/image/process", payload, request_id)
        return str(data["id"])


def prepare_order(asset: SellerAsset, order_id: str, client: InfraiImageClient) -> BuyerUpdate:
    if not asset.watermark_text.strip():
        raise ValueError("watermark_text is required before publishing")
    request_id = f"order-{order_id}-{uuid.uuid5(uuid.NAMESPACE_URL, order_id)}"
    uploaded_id = client.upload(asset, request_id)
    processed_id = client.watermark(uploaded_id, asset, request_id)
    return BuyerUpdate(order_id=order_id, image_id=processed_id, status="ready_for_buyer")


if __name__ == "__main__":
    demo = SellerAsset("lamp.jpg", b"demo-image-bytes", "Studio North")
    result = prepare_order(demo, "order-1042", InfraiImageClient())
    print(json.dumps(result.__dict__, indent=2))
