from fastapi import FastAPI
from fastapi.responses import JSONResponse

application = FastAPI()

N = 0

@application.get("/{whatever:path}")
def _(whatever: str) -> JSONResponse:
    global N
    N += 1
    return {"N": N, "whatever": whatever}
