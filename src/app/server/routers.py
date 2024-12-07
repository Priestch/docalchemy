from litestar import Litestar, get


@get("/")
async def hello_world() -> dict[str, str]:
    """Handler function that returns a greeting dictionary."""
    return {"hello": "world"}

