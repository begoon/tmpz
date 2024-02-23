from json import JSONDecodeError
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

application = FastAPI()


@application.post("/image")
async def image(
    request: Request,
    fields: list[str] = Form(None),
    files: list[UploadFile] = File(None),
):
    print(fields)
    print(files)
