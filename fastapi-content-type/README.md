# fastapi-content-type

<https://stackoverflow.com/questions/12667797/using-curl-to-upload-post-data-with-files>

```sh
curl -X POST -F "files=@main.py" -F "files=@README.md" http://localhost:8000/image
```

```log
None
[UploadFile(filename='main.py', size=393, headers=Headers({'content-disposition': 'form-data; name="files"; filename="main.py"', 'content-type': 'application/octet-stream'})), UploadFile(filename='README.md', size=315, headers=Headers({'content-disposition': 'form-data; name="files"; filename="README.md"', 'content-type': 'application/octet-stream'}))]
INFO:     127.0.0.1:52988 - "POST /image HTTP/1.1" 200 OK
```

```sh
curl -X POST -F "fields=main.py" -F "fields=README.md" http://localhost:8000/image
```

```log
['main.py', 'README.md']
None
INFO:     127.0.0.1:53031 - "POST /image HTTP/1.1" 200 OK
```
