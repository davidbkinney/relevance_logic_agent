import asyncio
import argparse
import sys
from pathlib import Path

from relevance_logic_agent import proof_generator

class TraceRecorder:
    def __init__(self, path: str | None):
        self.path = Path(path) if path else None
        self._file = None

        if self.path:
            self._file = open(self.path, "w", encoding="utf-8")

            self.emit("system", {
                "time": str(datetime.now()),
                "event": "session_start"
            })

    def emit(self, tag: str, data: dict):
        if not self._file:
            return
        self._file.write(f"\n[{tag}]\n{data}\n")
        self._file.flush()

    def write_raw(self, text: str):
        """THIS is the important part."""
        if self._file:
            self._file.write(text)
            self._file.flush()

    def close(self):
        if self._file:
            self._file.close()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--record", default=None)
    args = parser.parse_args()

    recorder = TraceRecorder(args.record)

    async def runner():
        recorder.write_raw(f"\n=== PROMPT ===\n{args.prompt}\n")

        # capture EVERYTHING printed
        buffer = StringIO()

        with redirect_stdout(buffer), redirect_stderr(buffer):
            result = await proof_generator.generate_proof(args.prompt)

        output = buffer.getvalue()

        # write full stream
        recorder.write_raw("\n=== FULL TRACE ===\n")
        recorder.write_raw(output)

        recorder.write_raw("\n=== FINAL OUTPUT ===\n")
        recorder.write_raw(result.final_output)

        recorder.close()

        print(result.final_output)

    asyncio.run(runner())

if __name__ == "__main__":
    main()
