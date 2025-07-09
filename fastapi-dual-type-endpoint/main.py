import json
from typing import Optional

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from pydantic import BaseModel

application = FastAPI()


class Payload(BaseModel):
    image: Optional[str] = None  # base64 encoded image
    data: str


@application.post("/process")
async def process(
    request: Request,
    multipart_json: Optional[UploadFile] = File(None),  # multipart/form-data
    multipart_image: Optional[UploadFile] = File(None),  # multipart/form-data
):
    contentType = request.headers.get("content-type")
    if contentType.startswith("application/json"):
        model_data = Payload(**(await request.json()))
        print("json model:", model_data)

        image = model_data.image
        print("json base64 image:", len(image))

    elif contentType.startswith("multipart/form-data"):
        model_data = Payload(**json.loads(await multipart_json.read()))
        print("multipart model:", model_data)

        image = await multipart_image.read()
        print("multipart binary image:", len(image))

    else:
        raise HTTPException(415, "unsupported media type")

    return {"ok": True}
