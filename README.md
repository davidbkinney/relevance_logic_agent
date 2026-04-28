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

This Python package allows users, with a single function call to: 

1. Enter natural-language queries to an LLM (GPT-5.4),
2. Launch an MCP server locally via stdio that exposes the LLM to a Python-based prover agent 
for the relevance logic R.
3. Receive as output a machine-verified proof of the requested proposition in the relevance
logic R (if such a proof exists), as well as a natural-language summary of the proof.

For very hard proofs, the LLM agent sometimes fails to find a valid proof even when one exists.
This in itself is interesting behavior; my intention with the project is to study the capabilities
and limitations of agentic provers for non-classical logics.

The agent is operated entirely from the command line. Here is a simple workflow to get started. 

First, install the package:

```bash
pip install git+https://github.com/davidbkinney/relevance_logic_agent
```



