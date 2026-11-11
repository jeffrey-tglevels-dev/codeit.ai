"""Delivery: source ZIP plus a Docker sandbox preview (data-models.md §11).

`image_built` and `healthy` are measured by code (build exit status, HTTP 200), never claimed.
"""

from datetime import datetime

from pydantic import BaseModel

from models.qa import TestReport


class ZipResult(BaseModel):
    zip_path: str  # "output/expense-tracker-<run_id>.zip"
    size_bytes: int


class SandboxResult(BaseModel):
    image_tag: str | None = None
    image_built: bool = False
    container_id: str | None = None
    host_port: int | None = None
    preview_url: str | None = None  # "http://localhost:9001"
    expires_at: datetime | None = None  # container is removed after this
    healthy: bool = False  # preview URL answered HTTP 200
    build_log_tail: str = ""
    notes: str = ""


class DeliveryResult(BaseModel):
    zip: ZipResult | None = None
    sandbox: SandboxResult | None = None
    test_report: TestReport | None = None  # attached, especially when not all tests passed
