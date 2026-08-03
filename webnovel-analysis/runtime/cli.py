import argparse
import json
import os
from pathlib import Path
import sys


if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from runtime.errors import RuntimeContractError
    from runtime.orchestrator import RuntimeOrchestrator
else:
    from .errors import RuntimeContractError
    from .orchestrator import RuntimeOrchestrator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Milestone 2 deterministic runtime")
    subcommands = parser.add_subparsers(dest="command", required=True)
    create = subcommands.add_parser("create")
    create.add_argument("--request", required=True, type=Path)
    run_batch = subcommands.add_parser("run-batch")
    run_batch.add_argument("--task", required=True)
    run_batch.add_argument("--batch", required=True)
    run_batch.add_argument("--adapter", choices=["fixture"], default="fixture")
    run_batch.add_argument("--scenario", default="valid")
    status = subcommands.add_parser("status")
    status.add_argument("--task", required=True)
    review = subcommands.add_parser("review")
    review.add_argument("--task", required=True)
    review.add_argument("--review", required=True)
    review.add_argument("--decision", choices=["ACCEPT", "REJECT_AND_RERUN", "ACCEPT_WITH_RISK"], required=True)
    review.add_argument("--reason", default="user decision")
    rerun = subcommands.add_parser("rerun")
    rerun.add_argument("--task", required=True)
    rerun.add_argument("--batch", required=True)
    rerun.add_argument("--module", required=True)
    rerun.add_argument("--adapter", choices=["fixture"], default="fixture")
    rerun.add_argument("--scenario", default="corrected")
    finalize = subcommands.add_parser("finalize")
    finalize.add_argument("--task", required=True)
    finalize.add_argument("--gate-c-decision", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    package_root = Path(__file__).resolve().parents[1]
    runs_root = Path(os.environ.get("WEBNOVEL_ANALYSIS_RUNS", package_root / "runs"))
    runtime = RuntimeOrchestrator(package_root=package_root, runs_root=runs_root)
    try:
        if args.command == "create":
            task = runtime.create_task(args.request)
            result = {"task_id": task.task_id, "status": task.status}
        elif args.command == "run-batch":
            batch = runtime.run_batch(args.task, args.batch, scenario=args.scenario)
            result = {"task_id": args.task, "batch_id": batch.batch_id, "status": batch.status}
        elif args.command == "status":
            task, batch = runtime.load_states(args.task)
            result = {"task": task.to_dict(), "batch": batch.to_dict(), "pending_reviews": runtime.pending_reviews(args.task)}
        elif args.command == "review":
            runtime.submit_review(args.task, args.review, args.decision, reason=args.reason)
            task, batch = runtime.load_states(args.task)
            result = {"task_id": args.task, "task_status": task.status, "batch_status": batch.status}
        elif args.command == "rerun":
            batch = runtime.rerun(args.task, args.batch, args.module, scenario=args.scenario)
            result = {"task_id": args.task, "batch_id": args.batch, "module_id": args.module, "status": batch.status}
        else:
            manifest = runtime.finalize(args.task, args.gate_c_decision)
            result = {"task_id": args.task, "status": "DELIVERABLE_READY", "manifest": str(manifest)}
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except RuntimeContractError as error:
        print(json.dumps({"error": {"code": error.code, "message": str(error), **error.context}}, ensure_ascii=False), file=sys.stderr)
        return 2
    except Exception as error:
        print(json.dumps({"error": {"code": "RUNTIME_EXECUTION_FAILED", "message": str(error)}}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
