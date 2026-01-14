from litestar import Litestar, get


@get("/")
async def index() -> str:
    return "abc!"


@get("/books/{book_id:int}")
async def get_book(book_id: int) -> dict[str, int]:
    return {"book_id": book_id}


application = Litestar([index, get_book])
