# P2 Integration Notes

Add these dependencies to the team's `requirements.txt`:

```text
google-cloud-vision>=3.10.0
serpapi>=0.1.5
Pillow>=10.0.0
```

Then in `main.py`:

```python
from search import search_web

p2_result = search_web(p1_result)
```

`p1_result` must contain `image_path`; `face_encoding` may be the encoding produced by P1.

The returned dictionary is ready to pass to P3/blockchain evidence handling.
