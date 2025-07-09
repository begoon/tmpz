# FastAPI dual type endpoint

1. application/json

```sh
curl -X POST http://localhost:8000/process -H "Content-Type: application/json" -d '{"image": "iVBORw0KGgoAAAANSUhE...", "data": "123" }' | jq
```

```json
{"ok":true}
```

and the output is:

```console
json model: image='iVBORw0KGgoAAAANSUhE' data='123'
json base64 image: 1474
```

1. multipart/form-data

```sh
curl -X POST http://localhost:8000/process -H "Content-Type: multipart/form-data" -F "multipart_json=@request.json" -F "multipart_image=@image.png" | jq
```

where "request.json" is:

```json
{ "data": "123" }
```

and the output is:

```console
multipart model: image=None data='123'
multipart binary image: 1474
```
