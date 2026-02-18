from __future__ import annotations

import time

import flask

from humblePhlipperPython.app.routes import bp as routes_bp
from humblePhlipperPython.config import settings
from humblePhlipperPython.services import scheduler

def create_app() -> flask.Flask:
    app = flask.Flask(__name__)
    app.register_blueprint(routes_bp)
    return app

def init_runtime() -> None:
    print("start scheduler.init()")
    t0 = time.perf_counter()
    scheduler.init()
    t1 = time.perf_counter()
    print("end scheduler.init()")
    print(f"{t1 - t0:.3f}s")

if __name__ == "__main__":
    init_runtime()
    app = create_app()
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False,
        threaded=True
    )