import argparse
import asyncio
from datetime import datetime
from pathlib import Path
from relevance_logic_agent import proof_generator

def write_record(path, prompt, output):
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        f.write("=== PROMPT ===\n")
        f.write(prompt + "\n\n")

        f.write("=== OUTPUT ===\n")
        f.write(output + "\n")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--record", type=str, default=None)

    args = parser.parse_args()

    async def runner():
        result = await proof_generator.generate_proof(args.prompt)

        output = result.final_output

        print(output)

        if args.record:
            write_record(args.record, args.prompt, output)

    asyncio.run(runner())

if __name__ == "__main__":
    main()
