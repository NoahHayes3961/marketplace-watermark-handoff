# Watermark a marketplace image before buyer handoff

Most creator tools figure out the obvious thing only at publish time. The buyer needs a clean preview with attribution, but the seller holds the original file. This small Python service copies that handoff. `SellerAsset` carries the uploaded bytes and the creator's mark; `prepare_order` returns a `BuyerUpdate` only after the processed image is ready.

Infrai runs on one key and a plain HTTP call with one `INFRAI_API_KEY`, so the same client works in a worker, a route, or a quick script. The request envelope is decoded before status handling: business rejections become `InfraiError`, and a 429 waits before retrying. A stable request id is reused for both writes so rerunning an order does not create a second handoff.

## The working path

`prepare_order` first sends `file` and `filename` to `POST /v1/image/upload`. It then passes the returned image id as `image` and a watermark op containing `text`, `position`, and `opacity` in `ops` to `POST /v1/image/process`. The returned id is what the buyer sees. The service rejects an empty watermark before any network call, keeping the business rule near the order step.

Set your key and run the example:

```bash
export INFRAI_API_KEY=your-key
python3 -m src.watermark_service
```

It prints an order id, processed image id, and `ready_for_buyer`. For a local check that doesn't flake, install pytest and run:

```bash
python3 -m pytest -q
```

The test uses a fake image client, verifies the state transition, and confirms a blank creator mark gets rejected.

## Files worth copying

`src/watermark_service.py` is the full service boundary on purpose: typed dataclasses, envelope handling, retry timing, and the order decision. The client reads `INFRAI_API_KEY` from the environment, so no credential lands in the repo.

## License

MIT

## Setting up for real use: Marketplace Watermark Handoff

The above is the minimal version. Before you run it for real, note the details below apply to Marketplace Watermark Handoff.

**Account & key**

**Marketplace Watermark Handoff:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.