"""``model learn`` — the learnability affordance.

Prints a structured self-teaching prompt with enough shape that an agent can
author its own usage skill without scraping ``--help``. Supports ``--json``.
"""

from __future__ import annotations

import argparse

from model_gear import __version__
from model_gear.cli._output import emit_result

_TEXT = """\
model-gear — run, assess, and switch the local vLLM model.

Purpose
-------
model-gear is the tooling that runs the local, OpenAI-compatible vLLM model the
Culture mesh consumes (the model-gear agent connects to it over the acp
`vllm-local` provider). It scaffolds a deployment, starts/stops the server,
switches which model is served, and assesses/benchmarks whatever is running —
producing the numbers in the per-model docs under docs/.

Commands
--------
  model init [TARGET]     Scaffold a deployment dir (default ~/.model-gear).
                          Dry-run by default; --apply to write, --force to overwrite.
  model serve             Start the vLLM server (alias: start). Dry-run; --apply.
  model stop              Stop the vLLM server. Dry-run; --apply.
  model switch <model>    Switch the served model. Dry-run; --apply recreates the
                          container and waits for /health.
  model fleet up|down|status
                          Drive the 2-model gateway deployment (scaffold it with
                          'model init --fleet'). up/down are dry-run; --apply.
  model status            Read-only: the warm (served) model, container state,
                          /health. (Catalog you can switch to: overview --list.)
  model assess            Read-only: correctness probes + reasoning-trace field.
  model benchmark         Read-only: decode throughput + prefill latency.
  model overview          Snapshot of the tool, the served model, and the supported
                          catalog (--current = warm model; --list = catalog).
  model whoami            Tool + machine + served model + container health.
  model explain <path>... Markdown docs for a topic (e.g. 'model explain switch').
  model doctor            Diagnose docker / compose / .env / health.

Mutation safety
---------------
Write verbs default to DRY RUN and require --apply to commit: `switch`, `serve`,
`stop`, `init`. Agents call CLIs in loops, so safe-by-default is mandatory. The
read-only verbs (`status`, `assess`, `benchmark`, `overview`, `whoami`,
`explain`, `doctor`) never change the world.

Models: supported vs. warm
--------------------------
Two different questions. The SUPPORTED CATALOG — the gears you can switch to, each
tagged load-tested or configured — is `model overview --list` (and the gateway's
GET /v1/models/supported); it is static, defined in model_gear/catalog.py and
shipped in the wheel. What's WARM right now (actually loaded in GPU memory) is GET
/v1/models, `model status`, or `model fleet status` — runtime truth that changes
when you switch or run the fleet. Mnemonic: the catalog is the menu; /v1/models is
what's hot now.

Machine-readable output
-----------------------
Every command supports --json. Errors in JSON mode emit
{"code", "message", "remediation"} to stderr. Stdout and stderr are never mixed.

Exit-code policy
----------------
  0 success
  1 user-input error (bad flag, bad path, missing arg)
  2 environment / setup error (docker missing, .env unreadable, endpoint down)
  3+ reserved

More detail
-----------
  model explain model-gear
  model explain switch
  model explain backend

Homepage: https://github.com/agentculture/model-gear
"""


def _as_json_payload() -> dict[str, object]:
    return {
        "tool": "model-gear",
        "version": __version__,
        "purpose": (
            "Tooling to run, assess, and switch the local vLLM model the Culture "
            "mesh consumes (the model-gear agent connects over the acp vllm-local provider)."
        ),
        "serves": "model-gear",
        "commands": [
            {"path": ["init"], "summary": "Scaffold a deployment dir (dry-run; --apply)."},
            {
                "path": ["serve"],
                "summary": "Start the vLLM server (alias: start; dry-run; --apply).",
            },
            {"path": ["stop"], "summary": "Stop the vLLM server (dry-run; --apply)."},
            {"path": ["switch"], "summary": "Switch the served model (dry-run; --apply)."},
            {
                "path": ["fleet"],
                "summary": "Drive the 2-model gateway deployment (up/down/status; --apply).",
            },
            {
                "path": ["status"],
                "summary": "Warm (served) model, state, /health; catalog: overview --list.",
            },
            {"path": ["assess"], "summary": "Correctness probes + reasoning-trace field."},
            {"path": ["benchmark"], "summary": "Decode throughput + prefill latency."},
            {
                "path": ["overview"],
                "summary": "Tool snapshot + served model + supported catalog (--current/--list).",
            },
            {"path": ["whoami"], "summary": "Tool, machine, served model, container health."},
            {"path": ["explain"], "summary": "Markdown docs by topic path."},
            {"path": ["doctor"], "summary": "Diagnose docker/compose/.env/health."},
        ],
        "mutation_safety": {
            "write_verbs": ["switch", "serve", "stop", "init", "fleet up", "fleet down"],
            "rule": "dry-run by default; require --apply to commit",
        },
        "exit_codes": {
            "0": "success",
            "1": "user-input error",
            "2": "environment/setup error",
        },
        "json_support": True,
        "models": {
            "supported_catalog": (
                "The gears you can switch to, each tagged load-tested/configured. Static "
                "(model_gear/catalog.py, shipped in the wheel). Read: 'model overview --list' "
                "or gateway GET /v1/models/supported."
            ),
            "warm_now": (
                "Model(s) actually loaded in GPU memory right now. Read: GET /v1/models, "
                "'model status', or 'model fleet status'. Changes when you switch or run the fleet."
            ),
        },
        "explain_pointer": "model explain <path> (e.g. 'model explain switch')",
    }


def cmd_learn(args: argparse.Namespace) -> int:
    json_mode = bool(getattr(args, "json", False))
    if json_mode:
        emit_result(_as_json_payload(), json_mode=True)
    else:
        emit_result(_TEXT, json_mode=False)
    return 0


def register(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "learn",
        help="Print a structured self-teaching prompt for agent consumers.",
    )
    p.add_argument("--json", action="store_true", help="Emit structured JSON.")
    p.set_defaults(func=cmd_learn)
