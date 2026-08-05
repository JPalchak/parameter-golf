import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def parse_required(pattern: str, text: str, label: str):
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        raise ValueError(f"Could not find {label} in train log")
    return match


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--author", required=True)
    parser.add_argument("--github-id", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--track", required=True)
    parser.add_argument("--train-log", required=True)
    parser.add_argument("--output", default="submission.json")
    parser.add_argument("--blurb", default="")
    args = parser.parse_args()

    log_path = Path(args.train_log)
    if not log_path.exists():
        raise FileNotFoundError(f"Train log not found: {log_path}")

    text = log_path.read_text(encoding="utf-8", errors="replace")

    exact = parse_required(
        r"final_int8_zlib_roundtrip_exact val_loss:(?P<val_loss>[-+0-9.eE]+) val_bpb:(?P<val_bpb>[-+0-9.eE]+)",
        text,
        "final exact roundtrip metrics",
    )
    pre = parse_required(
        r"step:(?P<step>\d+)/(?:\d+) val_loss:(?P<pre_val_loss>[-+0-9.eE]+) val_bpb:(?P<pre_val_bpb>[-+0-9.eE]+) train_time:(?P<train_time_ms>[-+0-9.eE]+)ms",
        text,
        "at least one validation line",
    )

    all_pre = list(
        re.finditer(
            r"step:(?P<step>\d+)/(?:\d+) val_loss:(?P<pre_val_loss>[-+0-9.eE]+) val_bpb:(?P<pre_val_bpb>[-+0-9.eE]+) train_time:(?P<train_time_ms>[-+0-9.eE]+)ms",
            text,
            re.MULTILINE,
        )
    )
    if all_pre:
        pre = all_pre[-1]

    bytes_model = parse_required(r"Serialized model int8\+zlib: (?P<bytes_model>\d+) bytes", text, "serialized int8+zlib bytes")
    bytes_code = parse_required(r"Code size: (?P<bytes_code>\d+) bytes", text, "code size")
    bytes_total = parse_required(r"Total submission size int8\+zlib: (?P<bytes_total>\d+) bytes", text, "total submission size")

    stop_match = re.search(r"stopping_early: wallclock_cap train_time:[-+0-9.eE]+ms step:(?P<step_stop>\d+)/(?:\d+)", text, re.MULTILINE)
    if stop_match:
        step_stop = int(stop_match.group("step_stop"))
    else:
        train_steps = list(re.finditer(r"step:(?P<step>\d+)/(?:\d+) train_loss:", text, re.MULTILINE))
        if not train_steps:
            raise ValueError("Could not infer final training step from log")
        step_stop = int(train_steps[-1].group("step"))

    payload = {
        "author": args.author,
        "github_id": args.github_id,
        "name": args.name,
        "blurb": args.blurb,
        "date": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "track": args.track,
        "val_loss": float(exact.group("val_loss")),
        "val_bpb": float(exact.group("val_bpb")),
        "pre_quant_val_loss": float(pre.group("pre_val_loss")),
        "pre_quant_val_bpb": float(pre.group("pre_val_bpb")),
        "step_stop": step_stop,
        "wallclock_seconds": float(pre.group("train_time_ms")) / 1000.0,
        "bytes_total": int(bytes_total.group("bytes_total")),
        "bytes_model_int8_zlib": int(bytes_model.group("bytes_model")),
        "bytes_code": int(bytes_code.group("bytes_code")),
    }

    output_path = Path(args.output)
    output_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
