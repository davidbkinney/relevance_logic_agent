import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime
from relevance_logic_agent import proof_generator


# ----------------------------
# Terminal Tee
# ----------------------------
class Tee:
    def __init__(self, file):
        self.file = file
        self.stdout = sys.stdout
        self.stderr = sys.stderr

    def write(self, data):
        self.stdout.write(data)
        if self.file:
            self.file.write(data)

    def flush(self):
        self.stdout.flush()
        if self.file:
            self.file.flush()


# ----------------------------
# Recorder
# ----------------------------
class TraceRecorder:
    def __init__(self, path: str | None):
        self.path = Path(path) if path else None
        self.file = None

        if self.path:
            self.file = open(self.path, "w", encoding="utf-8")

    def write_header(self, prompt: str):
        if not self.file:
            return
        self.file.write("\n=== PROMPT ===\n")
        self.file.write(prompt + "\n")
        self.file.write("\n=== RUN LOG ===\n\n")
        self.file.flush()

    def close(self):
        if self.file:
            self.file.close()


# ----------------------------
# CLI
# ----------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--record", default=None)
    args = parser.parse_args()

    recorder = TraceRecorder(args.record)

    async def runner():
        recorder.write_header(args.prompt)

        tee = None
        if args.record:
            f = open(args.record, "a", encoding="utf-8")

            tee = Tee(f)
            sys.stdout = tee
            sys.stderr = tee

        try:
            result = await proof_generator.generate_proof(args.prompt)

        finally:
            # restore terminal
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__

            if args.record:
                f.close()

        return result

    asyncio.run(runner())


if __name__ == "__main__":
    main()
