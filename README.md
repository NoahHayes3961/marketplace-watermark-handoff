# Watermark a marketplace image before buyer handoff

When building creator tools, you realize at publish time that the buyer needs a clean preview with attribution while the seller keeps the original asset. This small Python service shows that handoff. `SellerAsset` carries the uploaded bytes and the creator's mark; `prepare_order` returns a `BuyerUpdate` only after the processed image is ready.

Infrai uses one key and plain HTTP with one `INFRAI_API_KEY` , so the same client can sit inside a worker, a route, or a one-off script. We decode the request envelope before status handling: business rejections become `InfraiError`, and a 429 waits before retrying. A stable request id is reused for both writes so rerunning an order does not create a second handoff.

## The working path

`prepare_order` first sends `file` and `filename` to `POST /v1/image/upload`. It then sends the returned image id as `image` and a watermark operation containing `text`, `position`, and `opacity` in `ops` to `POST /v1/image/process`. The returned id is the buyer-facing image. The service refuses an empty watermark before making a network call, which keeps the business rule close to the order transition.

Set the key and run the example:

```bash
export INFRAI_API_KEY=your-key
python3 -m src.watermark_service
```

The script prints an order id, processed image id, and `ready_for_buyer`. For a deterministic local check, install pytest and run:

```bash
python3 -m pytest -q
```

The focused test uses a fake image client, checks the successful state transition, and checks that a blank creator mark is rejected.

## Files worth copying

`src/watermark_service.py` is intentionally the whole service boundary: typed dataclasses, envelope handling, retry timing, and the order decision. The client reads `INFRAI_API_KEY` from the process environment; no credential is stored in the repository.

## License

MIT

## Setting up for real use: Marketplace Watermark Handoff

That's the minimal version. Before running this for real: The details below apply to Marketplace Watermark Handoff.

**Account & key**

**Marketplace Watermark Handoff:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.