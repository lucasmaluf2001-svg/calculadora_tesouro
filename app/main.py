from __future__ import annotations

import json
import logging
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

from app.paths import ensure_runtime_snapshot, static_html_path
from app.services.snapshot import update_runtime_snapshot


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger("carteira_tesouro")

UPDATE_INTERVAL_SECONDS = 6 * 60 * 60  # checa 4 vezes ao dia; a fonte é diária.


def _safe_update() -> None:
    try:
        snapshot = update_runtime_snapshot()
        logger.info("Snapshot atualizado. Data-base: %s", snapshot.get("asof"))
    except Exception:
        logger.exception(
            "Falha ao atualizar. Mantendo o último snapshot válido."
        )


def _update_loop(stop_event: threading.Event) -> None:
    # Não bloqueia a subida do servidor: o snapshot-semente já permite servir
    # a página enquanto a primeira atualização é baixada em segundo plano.
    _safe_update()
    while not stop_event.wait(UPDATE_INTERVAL_SECONDS):
        _safe_update()


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_runtime_snapshot()
    stop = threading.Event()
    thread = threading.Thread(
        target=_update_loop,
        args=(stop,),
        daemon=True,
        name="snapshot-updater",
    )
    thread.start()
    app.state.stop_event = stop
    yield
    stop.set()


app = FastAPI(
    title="Carteira Histórica — Curva vs Mercado",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(static_html_path(), media_type="text/html")


@app.get("/calc_snapshot2.json", include_in_schema=False)
def snapshot():
    path = ensure_runtime_snapshot()
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return JSONResponse(
        content=data,
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


@app.get("/health", include_in_schema=False)
def health():
    path = ensure_runtime_snapshot()
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return {"status": "ok", "asof": data.get("asof")}
    except Exception as exc:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "detail": str(exc)},
        )
