from starlette.responses import Response


class YggResponseProcessor:
    def __init__(self, trace_id: str):
        self.trace_id = trace_id

    def process(self, response: Response) -> Response:
        response.headers["X-Trace-Id"] = self.trace_id
        return response
