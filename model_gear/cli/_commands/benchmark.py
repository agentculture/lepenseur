"""``model benchmark`` — decode throughput + prefill latency for the served model.

Read-only. Forces a fixed decode length over a couple of runs and measures a
large-prompt prefill, then emits a markdown block (plus host-side facts) for a
per-model doc under ``docs/``. Correctness lives in ``model assess``.
"""

from __future__ import annotations

import argparse

from model_gear import assess as _assess
from model_gear.cli import _runtime_ops
from model_gear.cli._output import emit_result
from model_gear.runtime import _compose, _env


def cmd_benchmark(args: argparse.Namespace) -> int:
    json_mode = bool(getattr(args, "json", False))
    port, deploy_dir = _runtime_ops.resolve_port_soft(args)
    model = args.model
    if model is None and deploy_dir is not None:
        model = _env.read_env(deploy_dir / _compose.ENV_FILE, "VLLM_SERVED_NAME")

    url = f"http://localhost:{port}"
    result = _assess.run_benchmark(url, model, decode_tokens=args.decode_tokens, runs=args.runs)
    host = {"image": _compose.container_image(), "gpu_memory": _compose.gpu_engine_mem()}

    if json_mode:
        emit_result({**result, "host": host}, json_mode=True)
    else:
        header = (
            "### Host-side\n"
            f"- Image: `{host['image']}`  ·  GPU memory (EngineCore): {host['gpu_memory']}\n"
        )
        emit_result(header + "\n" + _assess.render_benchmark(result), json_mode=False)
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "benchmark",
        help="Decode throughput + prefill latency for the served model (markdown for a doc).",
    )
    p.add_argument("--port", type=int, help="Host port (default: VLLM_PORT in .env, else 8000).")
    p.add_argument(
        "--model", help="Served model name (default: VLLM_SERVED_NAME, else first /v1/models)."
    )
    p.add_argument(
        "--decode-tokens", type=int, default=512, help="Forced decode length (default 512)."
    )
    p.add_argument("--runs", type=int, default=2, help="Decode-throughput repetitions (default 2).")
    p.add_argument(
        "--compose-dir", help="Deployment dir (default: $MODEL_GEAR_DIR or ~/.model-gear)."
    )
    p.add_argument("--json", action="store_true", help="Emit structured JSON.")
    p.set_defaults(func=cmd_benchmark)
