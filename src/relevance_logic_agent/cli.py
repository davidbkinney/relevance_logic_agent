import asyncio
import argparse
from relevance_logic_agent import proof_generator

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prompt", required=True)
    args = parser.parse_args()

    async def runner():
        result = await proof_generator.generate_proof(args.prompt)
        print(result.final_output)

    asyncio.run(runner())

if __name__ == "__main__":
    main()
