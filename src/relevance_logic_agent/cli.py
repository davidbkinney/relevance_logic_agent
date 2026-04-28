import asyncio
import argparse
import sys
from pathlib import Path

from relevance_logic_agent import proof_generator

import os
os.environ["OPENAI_AGENTS_DISABLE_TRACING"] = "1"

class TraceRecorder:
    def __init__(self, path):
        self.file = open(path, "w", encoding="utf-8") if path else None

        # save original stdout
        self._stdout = sys.stdout

        if self.file:
            sys.stdout = self

    def write(self, text):
        # write to terminal
        self._stdout.write(text)
        self._stdout.flush()

        # write to file
        if self.file:
            self.file.write(text)

    def flush(self):
        self._stdout.flush()
        if self.file:
            self.file.flush()

    def close(self):
        if self.file:
            sys.stdout = self._stdout
            self.file.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--record", default=None)
    args = parser.parse_args()

    recorder = TraceRecorder(args.record)

    async def runner():
        # 👇 THIS is the key change
        recorder.write("=== PROMPT ===")
        recorder.write(args.prompt)
        recorder.write("")

        result = await proof_generator.generate_proof(
            args.prompt,
            recorder=recorder
        )

        recorder.write("")
        recorder.write("=== FINAL RESULT ===")
        recorder.write(result.final_output)

        recorder.close()

        print(result.final_output)

    asyncio.run(runner())


if __name__ == "__main__":
    main()
