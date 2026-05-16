"""Estimate current slide-audio bitrate and compressed size targets."""

import argparse
import json
import subprocess
from pathlib import Path


def probe(path: Path) -> dict | None:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=codec_name,bit_rate,channels,sample_rate",
            "-show_entries",
            "format=duration,bit_rate,size",
            "-of",
            "json",
            str(path),
        ],
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="backend/content_builder/zh/integrated_chinese/artifacts/output_audio")
    parser.add_argument("--sample", type=int, default=300)
    args = parser.parse_args()

    files = sorted(Path(args.root).rglob("*slide*.mp3"))
    total_size = sum(path.stat().st_size for path in files)
    sample = files[:: max(1, len(files) // args.sample)][: args.sample]

    total_duration = 0.0
    bitrates = []
    channels = {}
    sample_rates = {}
    for path in sample:
        data = probe(path)
        if not data:
            continue
        fmt = data.get("format", {})
        stream = (data.get("streams") or [{}])[0]
        duration = float(fmt.get("duration") or 0)
        bitrate = int(stream.get("bit_rate") or fmt.get("bit_rate") or 0)
        total_duration += duration
        if bitrate:
            bitrates.append(bitrate)
        channels[stream.get("channels")] = channels.get(stream.get("channels"), 0) + 1
        sample_rates[stream.get("sample_rate")] = sample_rates.get(stream.get("sample_rate"), 0) + 1

    avg_bitrate = sum(bitrates) / len(bitrates) if bitrates else 0
    estimated_duration_all = total_duration * (len(files) / len(sample)) if sample else 0

    print(f"files={len(files)}")
    print(f"current_size={total_size / 1024 / 1024 / 1024:.2f} GB")
    print(f"sampled_files={len(sample)}")
    print(f"avg_bitrate={avg_bitrate / 1000:.1f} kbps")
    print(f"channels={channels}")
    print(f"sample_rates={sample_rates}")
    print(f"estimated_total_duration_hours={estimated_duration_all / 3600:.2f}")

    print("\nEstimated target sizes:")
    for kbps in (80, 64, 48, 40, 32):
        size_gb = estimated_duration_all * kbps * 1000 / 8 / 1024 / 1024 / 1024
        saved = total_size / 1024 / 1024 / 1024 - size_gb
        print(f"  {kbps:>3} kbps: {size_gb:.2f} GB  save {saved:.2f} GB")


if __name__ == "__main__":
    main()

