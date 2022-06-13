import uuid

import structlog
from flask import request


def enrich_structlog_with_request_context():
    structlog.threadlocal.clear_threadlocal()
    structlog.threadlocal.bind_threadlocal(
        blueprint=request.blueprint,
        view=request.path,
        method=request.method,
        scheme=request.scheme,
        request_id=str(uuid.uuid4()),
        peer=request.access_route[0],
        remote_addr=request.remote_addr,
    )
