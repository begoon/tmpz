from fastapi import FastAPI

application = FastAPI()


@application.get("/")
async def index():
    return {"message": "ha?"}


def main():
    print("UV!")


if __name__ == "__main__":
    main()
