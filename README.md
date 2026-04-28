# Relevance Logic Proving Agent

**N.B.: This project is in an experimental or "just for fun" stage.**

In classical logic, conditionals of the form "if P, then Q" are true whenever
P is false or Q is true. This verifies some strange conditionals, like:
"if snow is white then (if the moon is made of green cheese then the moon is made of green cheese)".
That such a conditional would be true seems to violate the commonsense notion that "if P, then Q"
can only be true when P is _relevant_ to Q in some sense. 

This has led many logicians to propose axiomatic systems meant to ensure that conditionals are
only true when the antecedent is relevant to the consequent. These are known as "relevance logics"
in American English and "relevant logics" in British English. Of these, the strongest well-known
system is the relevance logic R.

This repository implements a command line interface that allows users to, with a single command:

1. enter natural-language queries to an LLM (GPT-5.4),
2. launch an MCP server locally via stdio that exposes the LLM to a Python-based proof system 
for the relevance logic R, which the LLM can interact with agentically, and
3. receive as output a machine-verified proof of the requested proposition in the relevance
logic R (if such a proof exists), as well as a natural-language summary of the proof.

For very hard proofs, the LLM agent sometimes fails to find a valid proof even when one exists.
This in itself is interesting behavior; my intention with the project is to study the capabilities
and limitations of agentic provers for non-classical logics.

Here is a simple example workflow to get started. 

First, install the package:

```bash
pip install git+https://github.com/davidbkinney/relevance_logic_agent
```

Next, input your OpenAI API key.

```bash
OPENAI_API_KEY="YOUR KEY"
```

Finally, use the --prompt and --record flags to generate a proof and save it to a .txt file:

```bash
relevance-logic --prompt "Prove B from A and if A then B." --record modus_ponens.txt
```

Examples of this and the outputs of some other, more complex queries are included in this repository.


