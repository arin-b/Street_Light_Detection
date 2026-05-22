from __future__ import annotations

import json
import mimetypes
import urllib.parse
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from pathlib import Path
from typing import Any

from rbccps_annotator.auto_polygon import prompt_segmenter_status, propose_auto_polygon
from rbccps_annotator.schema import (
    ATTRIBUTION_CLASSES,
    LAMP_STATUS_CLASSES,
    LUX_POINT_TYPES,
    PUBLIC_SPACE_TYPES,
    SURFACE_TYPES,
    VISIBILITY_CLASSES,
)
from rbccps_annotator.workspace import item_lookup, load_manifest, load_review, save_review


class AnnotatorServer:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace.resolve()
        self.items = list(load_manifest(self.workspace).get("items", []))
        if not self.items:
            raise ValueError(f"Workspace has no items: {self.workspace}")
        self.item_by_key = {item["key"]: item for item in self.items}

    def bootstrap(self) -> dict[str, Any]:
        reviewed = 0
        for item in self.items:
            review = load_review(self.workspace, item)
            if review.get("review_status") and review.get("review_status") != "unreviewed":
                reviewed += 1
        return {
            "workspace": str(self.workspace),
            "total": len(self.items),
            "reviewed": reviewed,
            "modes": [
                "od_standard",
                "od_confounder",
                "track_review",
                "lamp_status",
                "public_space",
                "affected_region",
                "task_visibility",
                "attribution",
                "lux_reference",
                "qa",
            ],
            "surface_types": SURFACE_TYPES,
            "public_space_types": PUBLIC_SPACE_TYPES,
            "lamp_status_classes": LAMP_STATUS_CLASSES,
            "visibility_classes": VISIBILITY_CLASSES,
            "attribution_classes": ATTRIBUTION_CLASSES,
            "lux_point_types": LUX_POINT_TYPES,
            "auto_polygon": prompt_segmenter_status(),
        }

    def get_item(self, key: str | None = None, index: int | None = None) -> dict[str, Any]:
        if key:
            item = self.item_by_key.get(key)
            if not item:
                raise ValueError(f"Unknown key: {key}")
        else:
            item = self.items[max(0, min(index or 0, len(self.items) - 1))]
        item_index = self.items.index(item)
        return {
            "item": item,
            "review": load_review(self.workspace, item),
            "index": item_index,
            "total": len(self.items),
            "prev_key": self.items[item_index - 1]["key"] if item_index > 0 else None,
            "next_key": self.items[item_index + 1]["key"] if item_index + 1 < len(self.items) else None,
        }

    def image_path(self, key: str) -> Path:
        current = item_lookup(self.workspace).get(key)
        if not current:
            raise ValueError(f"Unknown key: {key}")
        path = Path(current["image_path"])
        if not path.exists():
            raise FileNotFoundError(path)
        return path

    def auto_polygon(self, payload: dict[str, Any]) -> dict[str, Any]:
        key = str(payload["item_key"])
        image_path = self.image_path(key)
        protected_boxes = payload.get("protected_boxes")
        if protected_boxes is None:
            item = self.item_by_key.get(key)
            protected_boxes = []
            if item:
                review = load_review(self.workspace, item)
                protected_boxes = [box.get("bbox_xyxy", []) for box in review.get("boxes", [])]
        return propose_auto_polygon(
            image_path=image_path,
            bbox_xyxy=[float(value) for value in payload["bbox_xyxy"]],
            protected_boxes=protected_boxes,
            margin_px=int(payload.get("margin_px", 12)),
        ).to_dict()


def run_server(workspace: Path, host: str, port: int, open_browser: bool) -> None:
    app = AnnotatorServer(workspace)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: object) -> None:
            return

        def _send_json(self, payload: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
            data = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_error_json(self, error: Exception, status: HTTPStatus = HTTPStatus.BAD_REQUEST) -> None:
            self._send_json({"error": str(error)}, status=status)

        def do_GET(self) -> None:
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)
            try:
                if parsed.path == "/":
                    return self._send_static("index.html")
                if parsed.path.startswith("/static/"):
                    return self._send_static(parsed.path.removeprefix("/static/"))
                if parsed.path == "/api/bootstrap":
                    return self._send_json(app.bootstrap())
                if parsed.path == "/api/item":
                    key = params.get("key", [None])[0]
                    index_text = params.get("index", [None])[0]
                    index = int(index_text) if index_text is not None else None
                    return self._send_json(app.get_item(key=key, index=index))
                if parsed.path == "/image":
                    key = params.get("key", [""])[0]
                    return self._send_file(app.image_path(key))
                self.send_error(HTTPStatus.NOT_FOUND)
            except FileNotFoundError as error:
                self._send_error_json(error, HTTPStatus.NOT_FOUND)
            except Exception as error:
                self._send_error_json(error)

        def do_POST(self) -> None:
            try:
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
                if self.path == "/api/save":
                    key = str(payload["key"])
                    review = payload["review"]
                    return self._send_json(save_review(app.workspace, key, review))
                if self.path == "/api/auto-polygon":
                    return self._send_json(app.auto_polygon(payload))
                self.send_error(HTTPStatus.NOT_FOUND)
            except Exception as error:
                self._send_error_json(error)

        def _send_static(self, name: str) -> None:
            try:
                data = resources.files("rbccps_annotator.static").joinpath(name).read_bytes()
            except FileNotFoundError:
                self.send_error(HTTPStatus.NOT_FOUND)
                return
            mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _send_file(self, path: Path) -> None:
            data = path.read_bytes()
            mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = ThreadingHTTPServer((host, port), Handler)
    url = f"http://{host}:{port}"
    print(f"RBCCPS annotator running at: {url}")
    print(f"Workspace: {app.workspace}")
    if open_browser:
        webbrowser.open(url)
    server.serve_forever()
