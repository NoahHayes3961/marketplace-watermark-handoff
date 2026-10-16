import pytest

from src.watermark_service import InfraiImageClient, SellerAsset, prepare_order


class FakeClient:
    def upload(self, asset, request_id):
        assert asset.filename == "lamp.jpg"
        return "uploaded-1"

    def watermark(self, image_id, asset, request_id):
        assert image_id == "uploaded-1"
        assert asset.watermark_text == "Studio North"
        return "processed-1"


def test_order_becomes_ready_after_watermarking():
    result = prepare_order(SellerAsset("lamp.jpg", b"x", "Studio North"), "order-1042", FakeClient())
    assert result.status == "ready_for_buyer"
    assert result.image_id == "processed-1"


def test_blank_watermark_is_rejected_before_upload():
    with pytest.raises(ValueError, match="watermark_text"):
        prepare_order(SellerAsset("lamp.jpg", b"x", "  "), "order-1042", FakeClient())


def test_process_request_uses_ops():
    client = InfraiImageClient(api_key="test-key")
    calls = []
    client._post = lambda path, payload, request_id: (calls.append((path, payload)), {"id": "processed-1"})[1]
    asset = SellerAsset("lamp.jpg", b"x", "Studio North")

    assert client.watermark("uploaded-1", asset, "request-1") == "processed-1"
    assert calls == [("/v1/image/process", {
        "image": "uploaded-1",
        "ops": [{"op": "watermark", "params": {"text": "Studio North", "position": "bottom-right", "opacity": 0.75}}],
    })]
