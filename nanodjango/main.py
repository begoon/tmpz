# /// script
# dependencies = ["nanodjango"]
# ///

from time import time

from django.db import models
from nanodjango import Django

app = Django()


@app.admin
class CountLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)


@app.route("/")
def count(request):
    CountLog.objects.create()
    return f"<p>number of page loads: {CountLog.objects.count()}</p>"


@app.api.get("/add")
def add(request):
    CountLog.objects.create()
    return {"count": CountLog.objects.count()}


@app.route("/slow/")
async def slow(request):
    import asyncio

    started = time()
    await asyncio.sleep(3)
    return f"async slow response: {time() - started:.2f}s"


if __name__ == "__main__":
    app.run()
