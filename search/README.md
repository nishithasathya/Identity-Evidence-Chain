# P2 — Web/Social Search Module

This module performs genuine live web/image discovery for the consenting demo image and returns the P2 → P3 evidence contract.

## Providers

1. **Google Cloud Vision Web Detection** is attempted first. It can return pages with matching images, matching image URLs, visually similar images, web entities, and best-guess labels.
2. **SerpApi Google Lens** is used as a fallback when Vision fails or produces no supported social-domain result.

## Supported social domains

- Instagram
- X / Twitter
- LinkedIn
- Facebook

## Input

```json
{
  "image_path": "sample_inputs/person.jpg",
  "face_encoding": []
}
```

The original image is used for reverse-image/web discovery. The face encoding is accepted as part of the P1 contract but is not sent to the web-search providers.

## Output

```json
{
  "matched_url": "https://...",
  "platform": "instagram",
  "image_url": "https://...",
  "caption": null,
  "author": null,
  "timestamp": null,
  "confidence": 0.90
}
```

Vision Web Detection does not reliably provide social-post captions, authors, or timestamps, so those fields may be `null`. SerpApi/Google Lens can provide richer metadata when available.

## Setup

Google Cloud Vision uses Application Default Credentials. Set `GOOGLE_APPLICATION_CREDENTIALS` to the service-account JSON path, or authenticate with the Google Cloud CLI.

For fallback search:

```bash
export SERPAPI_KEY="your-key"
```

Install dependencies from the project's `requirements.txt`.

## Run directly

From the repository root:

```bash
python -m search.search sample_inputs/person.jpg
```

## Limitations

- Search results depend on what Google Vision and Google Lens can index at run time.
- Social platforms may restrict crawling/indexing, so a real social post is not guaranteed for every image.
- Search results can change between runs.
- A reverse-image/web match is evidence of related online content, not proof of a person's identity.
- Confidence is a deterministic ranking score for this module; it is not a biometric identity probability.
- The module does not hardcode a social URL.
