"""
proof_generator.py

Contains functions to expose GPT-5.4 to the
MCP server and generate the proof.
"""

# Import packages.
from . import instructions, initialization
import asyncio
import sys
from pathlib import Path
import os
import time
from agents import Agent, Runner
from agents.mcp import MCPServerStdio


# Create a path to the MCP server.
server_path = (Path(__file__).parent / "mcp_server.py").resolve()

# Initialized the conncection to the OpenAI API.
def input_key(key: str):
    os.environ["OPENAI_API_KEY"] = key
    initialization.openai_setup(key)


# =========================
# GLOBAL RUN CONTROL
# =========================

RUN_LOCK = asyncio.Semaphore(1)


# =========================
# TOKEN PACER
# =========================

class TokenPacer:
    """
    Prevents token-per-minute bursts by spacing out Runner.run calls
    based on estimated token usage.
    """

    def __init__(self, max_tokens_per_min=3000):
        self.max_tokens_per_min = max_tokens_per_min
        self.window = []
        self.lock = asyncio.Lock()

    def _cleanup(self):
        now = time.monotonic()
        self.window = [t for t in self.window if now - t < 60]

    async def acquire(self, estimated_tokens: int):
        async with self.lock:
            while True:
                self._cleanup()
                current = sum(self.window)

                if current + estimated_tokens <= self.max_tokens_per_min:
                    self.window.append(estimated_tokens)
                    return

                await asyncio.sleep(0.5)


TOKEN_PACER = TokenPacer(max_tokens_per_min=25_000)


def estimate_tokens(text: str) -> int:
    """Estimates the number of tokens in a string."""
    return max(50, len(text) // 4)


# =========================
# TOOL TRACE WRAPPER
# =========================

class TracingMCPServer(MCPServerStdio):

    async def call_tool(self, name, arguments, **kwargs):
        print("\n🛠 TOOL CALL")
        print("Tool:", name)
        print("Args:", arguments)

        result = await super().call_tool(name, arguments, **kwargs)

        print("📤 TOOL RESULT")
        print(result)

        return result


# =========================
# RATE-LIMIT SAFE RUNNER
# =========================

async def run_with_token_pacing(agent, prompt, max_turns):
    estimated_tokens = estimate_tokens(prompt)

    await TOKEN_PACER.acquire(estimated_tokens)

    async with RUN_LOCK:
        return await Runner.run(
            agent,
            prompt,
            max_turns=max_turns,
        )



# =========================
# AGENT LOOP
# =========================

async def _run_agent(prompt: str):

    package_root = Path(__file__).resolve().parents[1]

    server_params = {
        "command": sys.executable,
        "args": ["-m", "relevance_logic_agent.mcp_server"],
        "cwd": str(package_root),
    }

    async with TracingMCPServer(params=server_params) as mcp_server:

        agent = Agent(
            name="Relevance Logic",
            instructions=instructions.INSTRUCTIONS,
            mcp_servers=[mcp_server],
            model="gpt-5.4",
        )

        print("\n=== RUNNING AGENT ===\n")

        result = await run_with_token_pacing(
            agent,
            prompt,
            max_turns=100,
        )

        print("\n=== FINAL RESULT ===\n")
        print(result.final_output)

        return result

# =========================
# USER-FACING PROOF GENERATION FUNCTION
# =========================

def generate_proof(prompt: str):
    return asyncio.run(_run_agent(prompt))


if __name__ == "__main__":
    print(generate_proof("test"))
