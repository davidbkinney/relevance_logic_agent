import asyncio
import os
from relevance_logic_agent import proof_generator

# Load API key safely
proof_generator.input_key(os.environ["OPENAI_API_KEY"])

prompt = """
Premises:
IF A THEN A
IF A THEN B
IF B THEN C

Goal:
IF A THEN C
"""

async def main():
    result = await proof_generator.generate_proof(prompt)

    print("\n=== FINAL RESULT ===\n")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())
