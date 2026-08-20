from __future__ import annotations

import threading
import webbrowser

import uvicorn


def open_browser():
    webbrowser.open("http://127.0.0.1:8765/")


def main():
    threading.Timer(1.5, open_browser).start()
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8765,
        log_level="info",
        reload=False,
    )


if __name__ == "__main__":
    main()
