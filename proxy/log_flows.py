"""
Addon do mitmproxy que registra TODAS as requisições que passam pelo proxy
reverso colocado na frente da API alvo.

Por que um proxy? Ele mede as três ferramentas exatamente do mesmo jeito
(número de requisições, operações exercitadas, respostas 5xx e o instante de
cada uma), sem depender do formato de relatório de cada ferramenta.

Saída: um JSON por linha em $FLOW_LOG (padrão /logs/flows.jsonl).
"""
import json
import os
import time

from mitmproxy import http

OUT = os.environ.get("FLOW_LOG", "/logs/flows.jsonl")
MAX_BODY = 4000


def _text(msg):
    try:
        return (msg.get_text(strict=False) or "")[:MAX_BODY]
    except Exception:
        return ""


class FlowLogger:
    def response(self, flow: http.HTTPFlow) -> None:
        req, resp = flow.request, flow.response
        rec = {
            "ts": time.time(),
            "method": req.method,
            "path": req.path.split("?", 1)[0],
            "query": req.path.split("?", 1)[1] if "?" in req.path else "",
            "req_headers": {k: v for k, v in req.headers.items() if k.lower() in ("content-type", "authorization")},
            "req_body": _text(req),
            "status": resp.status_code,
            "resp_body": _text(resp),
            "elapsed_ms": round((resp.timestamp_end - req.timestamp_start) * 1000, 1)
            if resp.timestamp_end and req.timestamp_start else None,
        }
        with open(OUT, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


addons = [FlowLogger()]
