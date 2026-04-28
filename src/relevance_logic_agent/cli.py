import asyncio
import argparse
import sys
from pathlib import Path

from relevance_logic_agent import proof_generator

import os
os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"

class Tee:
    """
    Duplicates stdout to both terminal and a file.
    """
    def __init__(self, file):
        self.file = file
        self.stdout = sys.stdout

    def write(self, data):
        self.stdout.write(data)
        self.file.write(data)

    def flush(self):
        self.stdout.flush()
        self.file.flush()


def start_record(path: str, prompt: str):
    """
    Start recording full CLI session (prompt + full stdout stream).
    """
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    f = open(path, "w", buffering=1)

    f.write("=== PROMPT ===\n")
    f.write(prompt + "\n\n")
    f.write("=== FULL TRACE ===\n")

    sys.stdout = Tee(f)

    return f


def stop_record(original_stdout, file_handle):
    """
    Restore stdout and close file safely.
    """
    sys.stdout = original_stdout
    if file_handle:
        file_handle.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument(
        "--record",
        type=str,
        default=None,
        help="Path to save full execution trace (prompt + MCP stream + output)"
    )

    args = parser.parse_args()

    original_stdout = sys.stdout
    record_file = None

    # Start recording if requested
    if args.record:
        record_file = start_record(args.record, args.prompt)

    async def runner():
        result = await proof_generator.generate_proof(args.prompt)

        print("\n=== FINAL RESULT ===\n")
        print(result.final_output)

    try:
        asyncio.run(runner())
    finally:
        stop_record(original_stdout, record_file)


if __name__ == "__main__":
    main()
