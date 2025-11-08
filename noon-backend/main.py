from __future__ import annotations

import os

import uvicorn

from noon_backend import create_app

app = create_app()


def run() -> None:
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "true").lower() == "true",
    )


if __name__ == "__main__":
    run()

