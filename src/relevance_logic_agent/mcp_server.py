"""
mcp_server.py

Constructs the tools needed to implement a relevanc
logic prover, and exposes them to the LLM agent.
"""

#Import Packages
from fastmcp import FastMCP
from pydantic import BaseModel, Field

#Create the server.
mcp = FastMCP("Relevance Logic")

# =========================
# Define Classes
# =========================


#WFF (well-formed formula) class
class WFF(BaseModel):
    id: int # WFF ID number
    kind: str # atom, negation, conditional, disjunction, conjunction
    value: str | None = None # The text of an atom
    child: int | None = None # The negated WFF
    left: int | None = None  # WFF on the left of a conditional, conjunction, or disjunction
    right: int | None = None # WFF on the right of conditional, conjunction, or disjunction

# Proof step class
class ProofStep(BaseModel):
    id: int # WFF ID number
    rule: str # Rule that allowed the WFF to be added to the proof
    args: list[int] = Field(default_factory=list) # Arguments to the rule that allowed it to be added to the proof.

# Class specifying the state of reasoning 
# (all WFFs and proof steps).
class State(BaseModel):
    update_num: int = 1 #Number that increments every time the state is updated.
    wffs: dict[int, WFF] = Field(default_factory=dict) # List of all WFFs available for use.
    proof: list[ProofStep] = Field(default_factory=list) # List of all steps in the proof.

#Create the global reasoning state.
STATE = State() 


# =========================
# Helper Functions
# =========================

def store(wff: WFF) -> int:
    """
    Adds each WFF to the list of available WFFs in the state, and 
    assigns it an ID if it does not already have one.

    Args:
        wff: A WFF object

    Returns:
        The integer ID assigned to the WFF.
    """
    global STATE

    key = (wff.kind, wff.value, wff.child, wff.left, wff.right)

    for existing in STATE.wffs.values():
        if (existing.kind, existing.value, existing.child,
            existing.left, existing.right) == key:
            return existing.id

    wff.id = STATE.update_num
    STATE.wffs[wff.id] = wff
    STATE.update_num += 1
    return wff.id


def require(id: int) -> WFF:
    """
    Checks that an integer is an ID assigned to a WFF, and returns
    that WFF if it exists.
    """
    wff = STATE.wffs.get(id)
    if wff is None:
        raise ValueError(f"WFF {id} does not exist")
    return wff


def in_proof(id: int) -> bool:
    """
    Checks that a WFF is in the proof.
    """
    return (
        any(s.id == id for s in STATE.proof)
    )

def state_update(wff: WFF | None = None, 
                 proof_added: ProofStep | None = None) -> dict:
    """
    Returns a description of an update to the state.

    Args:
        WFF (optional): The WFF added to the list of WFFs in the state.
        proof_added (optional): The WFF added to the proof in the state.

    Returns:
        A dictionary decribing the updates to the state.
    """
    return {
        "update_num": STATE.update_num,
        "wff": wff.model_dump() if wff else None,
        "proof_added": proof_added.model_dump() if proof_added else None,
    }

def render_wff(wff: WFF) -> str:
    """
    Renders a logical depiction of a WFF.
    """
    if wff.kind == "atom":
        return wff.value

    if wff.kind == "conditional":
        return f"({wff.left} → {wff.right})"

    if wff.kind == "conjunction":
        return f"({wff.left} ∧ {wff.right})"

    if wff.kind == "disjunction":
        return f"({wff.left} ∨ {wff.right})"

    if wff.kind == "negation":
        return f"¬{wff.child}"

    return f"<unknown:{wff.id}>"


def render_state_view() -> dict:
    """
    Displays the rendered view of the full state of the
    system.
    """
    return {
        "wffs": {
            wid: {
                "repr": render_wff(w),
                "id": w.id
            }
            for wid, w in STATE.wffs.items()
        },
        "proof": [
            {
                "step": i,
                "wff": render_wff(STATE.wffs[s.id]),
                "rule": s.rule,
                "args": s.args
            }
            for i, s in enumerate(STATE.proof)
        ],
        "update_num": STATE.update_num
    }


# =========================
# Constructor Functions
# =========================

@mcp.tool()
def atom(value: str) -> dict:
    """
    Adds an atom to the list of available WFFs.
    
    Args:
        value: A string description of the atom to be added.

    Returns:
        A dict describing the atom added to the list of 
        available WFFs.
    """
    w_id = store(WFF(
        id=0,
        kind="atom",
        value=value
    ))

    return state_update(wff=STATE.wffs[w_id])


@mcp.tool()
def negation(child_id: int):
    """
    Adds an negated WFF to the list of available WFFs.
    
    Args:
        child_id: A the ID of the WFF to be negated.

    Requirements:
        child_id must pick out a WFF already in the list
        of available WFFs.

    Returns:
        A dict describing the negation added to the list of 
        available WFFs.
    """
    require(child_id)

    w_id = store(WFF(
        id=0,
        kind="negation",
        child=child_id
    ))

    return state_update(wff=STATE.wffs[w_id])


@mcp.tool()
def conditional(antecedent_id: int, consequent_id: int):
    """
    Adds a conditional WFF to the list of available WFFs.
    
    Args:
        antecedent_id: The ID of the antecedent of the conditional.
        consequent_id: The ID of the conseuqent of the conditional.

    Requirements:
        antecedent_id and consequent_id must pick out a WFF already 
        in the list of available WFFs.

    Returns:
        A dict describing the conditional added to the list of 
        available WFFs.
    """
    require(antecedent_id)
    require(consequent_id)

    w_id = store(WFF(
        id=0,
        kind="conditional",
        left=antecedent_id,
        right=consequent_id
    ))

    return state_update(wff=STATE.wffs[w_id])


@mcp.tool()
def conjunction(conjunct1_id: int, conjunct2_id: int):
    """
    Adds a conjunction to the list of available WFFs.
    
    Args:
        conjunct1_id: The ID of the first conjunct.
        conjunct2_id: The ID of the second conjunct.

    Requirements:
        conjunct1_id and conjunct2_id must pick out a WFF already 
        in the list of available WFFs.

    Returns:
        A dict describing the conjunction added to the list of 
        available WFFs.
    """
    require(conjunct1_id)
    require(conjunct2_id)

    w_id = store(WFF(
        id=0,
        kind="conjunction",
        left=conjunct1_id,
        right=conjunct2_id
    ))

    return state_update(wff=STATE.wffs[w_id])


@mcp.tool()
def disjunction(disjunct1_id: int, disjunct2_id: int):
    """
    Adds a disjunction to the list of available WFFs.
    
    Args:
        disjunct1_id: The ID of the first disjunct.
        disjunct2_id: The ID of the second disjunct.

    Requirements:
        disjunct1_id and disjunct2_id must pick out a WFF already 
        in the list of available WFFs.

    Returns:
        A dict describing the disjunction added to the list of 
        available WFFs.
    """
    require(disjunct1_id)
    require(disjunct2_id)

    w_id = store(WFF(
        id=0,
        kind="disjunction",
        left=disjunct1_id,
        right=disjunct2_id
    ))

    return state_update(wff=STATE.wffs[w_id])


# =========================
# Adding Premises
# =========================


@mcp.tool()
def add_premise(id: int) -> dict:
    """Adds a WFF from the bank into the proof.
    
    IMPORTANT: This must be called before any inference rule 
    can use a WFF that has not been derived or added to the 
    proof as an axiom. WFFs in WFFBank are NOT automatically 
    in the list of proofs.

    Args: 
        id: the ID of an available WFF.

    Requirements:
        id must pick out a WFF already in the list
        of available WFFs.

    Returns:
        A dict describing the WFF added to the proof.
    """
    require(id)

    step = ProofStep(id=id, rule="premise")

    STATE.proof.append(step)

    return state_update(wff=STATE.wffs[id],proof_added=step)


# =========================
# Axioms
# =========================


@mcp.tool()
def identity(a_id:int) -> dict:
    """
    Adds an axiom of the form A → A to the proof. 

    Args: 
        a_id: the ID of an available WFF to be substituted
        as A in the axiom schema.

    Requirements:
        a_id must pick out a WFF already in the list
        of available WFFs.

    Returns:
        A dict describing the WFF added to the proof.
    """
    A = require(a_id)

    new_id = store(WFF(
        id=0,
        kind="conditional",
        left=A.id,
        right=A.id
    ))

    step = ProofStep(
            id=new_id,
            rule="Axiom (Identity)"
        )

    STATE.proof.append(step)

    return state_update(wff=STATE.wffs[new_id], proof_added=step)

@mcp.tool()
def sufffixing(a_id:int, b_id:int, c_id:int) -> dict:
    """
    Adds an axiom of the form (A → B) → ((B → C) → (A → C)) 
    to the proof. 

    Args: 
        a_id: the ID of an available WFF to be substituted
        as A in the axiom schema.
        b_id: the ID of an available WFF to be substituted
        as B in the axiom schema.
        c_id: the ID of an available WFF to be substituted
        as C in the axiom schema.

    Requirements:
        a_id, b_id, and c_id must pick out a WFF already in 
        the list of available WFFs.

    Returns:
        A dict describing the WFF added to the proof.
    """
    A = require(a_id)
    B = require(b_id)
    C = require(c_id)

    antecedent_id = store(WFF(
        id=0,
        kind="conditional",
        left=A.id,
        right=B.id
    ))

    consequent_antecedent_id = store(WFF(
        id=0,
        kind="conditional",
        left=B.id,
        right=C.id
    ))

    consequent_consequent_id = store(WFF(
        id=0,
        kind="conditional",
        left=A.id,
        right=C.id
    ))

    consequent_id = store(WFF(
        id=0,
        kind="conditional",
        left=consequent_antecedent_id,
        right=consequent_consequent_id
    ))

    new_id = store(WFF(
        id=0,
        kind="conditional",
        left=antecedent_id,
        right=consequent_id
    ))

    step = ProofStep(
        id=new_id,
        rule="Axiom (Suffixing)"
    )

    STATE.proof.append(step)

    return state_update(wff=STATE.wffs[new_id], proof_added=step)


@mcp.tool()
def contraction(a_id:int, b_id:int) -> dict:
    """
    Adds an axiom of the form (A → (A → B)) → (A → B) to the proof. 

    Args: 
        a_id: the ID of an available WFF to be substituted
        as A in the axiom shema.
        b_id: the ID of an available WFF to be substituted
        as B in the axiom shema.

    Requirements:
        a_id and b_id must pick out a WFF already in 
        the list of available WFFs.

    Returns:
        A dict describing the WFF added to the proof.
    """
    A = require(a_id)
    B = require(b_id)

    antecedent_consequent_id = store(WFF(
        id=0,
        kind="conditional",
        left=A.id,
        right=B.id
    ))


    antecedent_id = store(WFF(
        id=0,
        kind="conditional",
        left=A.id,
        right=antecedent_consequent_id
    ))


    new_id = store(WFF(
        id=0,
        kind="conditional",
        left=antecedent_id,
        right=antecedent_consequent_id
    ))

    step = ProofStep(
            id=new_id,
            rule="Axiom (Contraction)"
        )

    STATE.proof.append(step)

    return state_update(wff=STATE.wffs[new_id], proof_added=step)


@mcp.tool()
def assertion(a_id:int, b_id:int) -> dict:
    """
    Adds an axiom of the form A → ((A → B) →  B)) to the proof. 

    Args: 
        a_id: the ID of an available WFF to be substituted
        as A in the axiom schema.
        b_id: the ID of an available WFF to be substituted
        as B in the axiom schema.

    Requirements:
        a_id and b_id must pick out a WFF already in 
        the list of available WFFs.

    Returns:
        A dict describing the WFF added to the proof.
    """
    A = require(a_id)
    B = require(b_id)

    consequent_antecedent_id = store(WFF(
        id=0,
        kind="conditional",
        left=A.id,
        right=B.id
    ))

    consequent_id = store(WFF(
        id=0,
        kind="conditional",
        left=consequent_antecedent_id,
        right=B.id
    ))

    new_id = store(WFF(
        id=0,
        kind="conditional",
        left=A.id,
        right=consequent_id
    ))


    step = ProofStep(
        id=new_id,
        rule="Axiom (Assertion)"
    )

    STATE.proof.append(step)

    return state_update(wff=STATE.wffs[new_id], proof_added=step)


@mcp.tool()
def conjunction_introduction(a_id:int, b_id:int,
                                   c_id:int) -> dict:
    """
    Adds an axiom of the form ((A → B) &  (A → C)) → (A → (B & C)) 
    to the proof. 

    Args: 
        a_id: the ID of an available WFF to be substituted
        as A in the axiom schema.
        b_id: the ID of an available WFF to be substituted
        as B in the axiom schema.
        c_id: the ID of an available WFF to be substituted
        as C in the axiom schema.

    Requirements:
        a_id, b_id, and c_id must pick out a WFF already in 
        the list of available WFFs.

    Returns:
        A dict describing the WFF added to the proof.
    """
    A = require(a_id)
    B = require(b_id)
    C = require(c_id)

    antecedent_antecedent_id = store(WFF(
        id=0,
        kind="conditional",
        left=A.id,
        right=B.id
    ))

    antecedent_consequent_id = store(WFF(
        id=0,
        kind="conditional",
        left=A.id,
        right=C.id
    ))

    antecedent_id = store(WFF(
        id=0,
        kind="conjunction",
        left=antecedent_antecedent_id,
        right=antecedent_consequent_id
    ))

    consequent_consequent_id = store(WFF(
        id=0,
        kind="conjunction",
        left=B.id,
        right=C.id
    ))

    consequent_id = store(WFF(
        id=0,
        kind="conditional",
        left=A.id,
        right=consequent_consequent_id
    ))

    new_id = store(WFF(
        id=0,
        kind="conditional",
        left=antecedent_id,
        right=consequent_id
    ))


    step = ProofStep(
            id=new_id,
            rule="Axiom (Conjunction Introduction)"
        )

    STATE.proof.append(step)

    return state_update(wff=STATE.wffs[new_id], proof_added=step)



@mcp.tool()
def conjunction_elimination_left(a_id:int, b_id:int):
    """
    Adds an axiom of the form (A & B) → A)) to the proof. 

    Args: 
        a_id: the ID of an available WFF to be substituted
        as A in the axiom schema.
        b_id: the ID of an available WFF to be substituted
        as B in the axiom schema.

    Requirements:
        a_id and b_id must pick out a WFF already in 
        the list of available WFFs.

    Returns:
        A dict describing the WFF added to the proof.    
    """
    A = require(a_id)
    B = require(b_id)

    antecedent_id = store(WFF(
        id=0,
        kind="conjunction",
        left=A.id,
        right=B.id
    ))

    new_id = store(WFF(
        id=0,
        kind="conditional",
        left=antecedent_id,
        right=A.id
    ))

    step = ProofStep(
        id=new_id,
        rule="Axiom (Conjunction Elimination)"
    )

    STATE.proof.append(step)

    return state_update(wff=STATE.wffs[new_id], proof_added=step)


@mcp.tool()
def conjunction_elimination_right(a_id:int, b_id:int):
    """
    Adds an axiom of the form (A & B) → B)) to the proof. 

    Args: 
        a_id: the ID of an available WFF to be substituted
        as A in the axiom schema.
        b_id: the ID of an available WFF to be substituted
        as B in the axiom schema.

    Requirements:
        a_id and b_id must pick out a WFF already in 
        the list of available WFFs.

    Returns:
        A dict describing the WFF added to the proof.
    """
    A = require(a_id)
    B = require(b_id)

    antecedent_id = store(WFF(
        id=0,
        kind="conjunction",
        left=A.id,
        right=B.id
    ))

    new_id = store(WFF(
        id=0,
        kind="conditional",
        left=antecedent_id,
        right=B.id
    ))

    step = ProofStep(
        id=new_id,
        rule="Axiom (Conjunction Elimination)"
    )

    STATE.proof.append(step)

    return state_update(wff=STATE.wffs[new_id], proof_added=step)


@mcp.tool()
def disjunction_introduction_left(a_id:int, b_id:int):
    """
    Adds an axiom of the form A → (A v B) to the proof. 

    Args: 
        a_id: the ID of an available WFF to be substituted
        as A in the axiom schema.
        b_id: the ID of an available WFF to be substituted
        as B in the axiom schema.

    Requirements:
        a_id and b_id must pick out a WFF already in 
        the list of available WFFs.

    Returns:
        A dict describing the WFF added to the proof.
    """
    A = require(a_id)
    B = require(b_id)

    consequent_id = store(WFF(
        id=0,
        kind="disjunction",
        left=A.id,
        right=B.id
    ))

    new_id = store(WFF(
        id=0,
        kind="conditional",
        left=A.id,
        right=consequent_id
    ))

    step = ProofStep(
        id=new_id,
        rule="Axiom (Disjunction Introduction)"
    )

    STATE.proof.append(step)

    return state_update(wff=STATE.wffs[new_id], proof_added=step)



@mcp.tool()
def disjunction_introduction_right(a_id:int, b_id:int):
    """
    Adds an axiom of the form B → (A v B) to the proof. 

    Args: 
        a_id: the ID of an available WFF to be substituted
        as A in the axiom schema.
        b_id: the ID of an available WFF to be substituted
        as B in the axiom schema.

    Requirements:
        a_id and b_id must pick out a WFF already in 
        the list of available WFFs.

    Returns:
        A dict describing the WFF added to the proof.
    """
    A = require(a_id)
    B = require(b_id)

    consequent_id = store(WFF(
        id=0,
        kind="disjunction",
        left=A.id,
        right=B.id
    ))

    new_id = store(WFF(
        id=0,
        kind="conditional",
        left=B.id,
        right=consequent_id
    ))

    step = ProofStep(
        id=new_id,
        rule="Axiom (Disjunction Introduction)"
    )

    STATE.proof.append(step)

    return state_update(wff=STATE.wffs[new_id], proof_added=step)


@mcp.tool()
def disjunction_elimination1(a_id:int, b_id:int, c_id:int):
    """
    Adds an axiom of the form ((A v B) → C) → ((A → B) & (B → C)) 
    to the proof. 

    Args: 
        a_id: the ID of an available WFF to be substituted
        as A in the axiom schema.
        b_id: the ID of an available WFF to be substituted
        as B in the axiom schema.
        c_id: the ID of an available WFF to be substituted
        as C in the axiom schema.

    Requirements:
        a_id, b_id, and c_id must pick out a WFF already in 
        the list of available WFFs.

    Returns:
        A dict describing the WFF added to the proof.
    """
    A = require(a_id)
    B = require(b_id)
    C = require(c_id)

    antecedent_antecedent_id = store(WFF(
        id=0,
        kind="disjunction",
        left=A.id,
        right=B.id
    ))

    antecedent_id = store(WFF(
        id=0,
        kind="conditional",
        left=antecedent_antecedent_id,
        right=C.id
    ))

    consequent_left_id = store(WFF(
        id=0,
        kind="conditional",
        left=A.id,
        right=B.id
    ))

    consequent_right_id = store(WFF(
        id=0,
        kind="conditional",
        left=B.id,
        right=C.id
    ))

    consequent_id = store(WFF(
        id=0,
        kind="conjunction",
        left=consequent_left_id,
        right=consequent_right_id
    ))

    new_id = store(WFF(
        id=0,
        kind="conditional",
        left=antecedent_id,
        right=consequent_id
    ))

    step = ProofStep(
        id=new_id,
        rule="Axiom (Disjunction Elimination)"
    )

    STATE.proof.append(step)

    return state_update(wff=STATE.wffs[new_id], proof_added=step)


@mcp.tool()
def disjunction_elimination2(a_id:int, b_id:int, c_id:int):
    """
    Adds an axiom of the form ((A → B) & (B → C)) → ((A v B) → C) 
    to the proof. 

    Args: 
        a_id: the ID of an available WFF to be substituted
        as A in the axiom schema.
        b_id: the ID of an available WFF to be substituted
        as B in the axiom schema.
        c_id: the ID of an available WFF to be substituted
        as C in the axiom schema.

    Requirements:
        a_id, b_id, and c_id must pick out a WFF already in 
        the list of available WFFs.

    Returns:
        A dict describing the WFF added to the proof.
    """
    A = require(a_id)
    B = require(b_id)
    C = require(c_id)

    antecedent_left_id = store(WFF(
        id=0,
        kind="conditional",
        left=A.id,
        right=B.id
    ))

    antecedent_right_id = store(WFF(
        id=0,
        kind="conditional",
        left=B.id,
        right=C.id
    ))

    antecedent_id = store(WFF(
        id=0,
        kind="conjunction",
        left=antecedent_left_id,
        right=antecedent_right_id
    ))

    consequent_antecedent_id = store(WFF(
        id=0,
        kind="disjunction",
        left=A.id,
        right=B.id
    ))

    consequent_id = store(WFF(
        id=0,
        kind="conditional",
        left=consequent_antecedent_id,
        right=C.id
    ))

    new_id = store(WFF(
        id=0,
        kind="conditional",
        left=antecedent_id,
        right=consequent_id
    ))

    step = ProofStep(
        id=new_id,
        rule="Axiom (Disjunction Elimination)"
    )

    STATE.proof.append(step)

    return state_update(wff=STATE.wffs[new_id], proof_added=step)



@mcp.tool()
def distribution(a_id:int, b_id:int, c_id:int):
    """
    Adds an axiom of the form ((A & (B v C)) → ((A & B) v (A & C)) 
    to the proof. 

    Args: 
        a_id: the ID of an available WFF to be substituted
        as A in the axiom schema.
        b_id: the ID of an available WFF to be substituted
        as B in the axiom schema.
        c_id: the ID of an available WFF to be substituted
        as C in the axiom schema.

    Requirements:
        a_id, b_id, and c_id must pick out a WFF already in 
        the list of available WFFs.

    Returns:
        A dict describing the WFF added to the proof.
    """
    A = require(a_id)
    B = require(b_id)
    C = require(c_id)

    antecedent_right_id = store(WFF(
        id=0,
        kind="disjunction",
        left=B.id,
        right=C.id
    ))

    antecedent_id = store(WFF(
        id=0,
        kind="conjunction",
        left=A.id,
        right=antecedent_right_id
    ))

    consequent_left_id = store(WFF(
        id=0,
        kind="conjunction",
        left=A.id,
        right=B.id
    ))

    consequent_right_id = store(WFF(
        id=0,
        kind="conjunction",
        left=A.id,
        right=C.id
    ))

    consequent_id = store(WFF(
        id=0,
        kind="disjunction",
        left=consequent_left_id,
        right=consequent_right_id
    ))

    new_id = store(WFF(
        id=0,
        kind="conditional",
        left=antecedent_id,
        right=consequent_id
    ))

    step = ProofStep(
        id=new_id,
        rule="Axiom (Distribution)"
    )

    STATE.proof.append(step)

    return state_update(wff=STATE.wffs[new_id], proof_added=step)


@mcp.tool()
def contraposition(a_id:int, b_id:int):
    """
    Adds an axiom of the form (A → ¬B) → (B → ¬A) to the proof. 

    Args: 
        a_id: the ID of an available WFF to be substituted
        as A in the axiom schema.
        b_id: the ID of an available WFF to be substituted
        as B in the axiom schema.

    Requirements:
        a_id and b_id must pick out a WFF already in 
        the list of available WFFs.

    Returns:
        A dict describing the WFF added to the proof.
    """
    A = require(a_id)
    B = require(b_id)

    neg_B_id = store(WFF(
        id=0,
        kind="negation",
        child=B.id
    ))

    antecedent_id = store(WFF(
        id=0,
        kind="conditional",
        left=A.id,
        right=neg_B_id
    ))

    neg_A_id = store(WFF(
        id=0,
        kind="negation",
        child=A.id
    ))

    consequent_id = store(WFF(
        id=0,
        kind="conditional",
        left=B.id,
        right=neg_A_id
    ))

    new_id = store(WFF(
        id=0,
        kind="conditional",
        left=antecedent_id,
        right=consequent_id
    ))

    step = ProofStep(
        id=new_id,
        rule="Axiom (Contraposition)"
    )

    STATE.proof.append(step)

    return state_update(wff=STATE.wffs[new_id], proof_added=step)


@mcp.tool()
def double_negation(a_id:int):
    """
    Adds an axiom of the form ¬¬A → A to the proof. 

    Args: 
        a_id: the ID of an available WFF to be substituted
        as A in the axiom schema.

    Requirements:
        a_id must pick out a WFF already in 
        the list of available WFFs.

    Returns:
        A dict describing the WFF added to the proof.
    """
    A = require(a_id)

    neg1_id = store(WFF(
        id=0,
        kind="negation",
        child=A.id
    ))

    antecedent_id = store(WFF(
        id=0,
        kind="negation",
        child=neg1_id
    ))

    new_id = store(WFF(
        id=0,
        kind="conditional",
        left=antecedent_id,
        right=A.id
    ))

    step = ProofStep(
        id=new_id,
        rule="Axiom (Double Negation)"
    )

    STATE.proof.append(step)

    return state_update(wff=STATE.wffs[new_id], proof_added=step)


# =========================
# Inference Rules
# =========================

@mcp.tool()
def modus_ponens(conditional_id: int):
    """
    Makes an inference of the form:

    A, A → B ⟹ B

    Args:
        conditional_id: The id number for a conditional WFF.

    Requirements:

        conditional_id and its antecedent (i.e., the WFF in the 
        left position of the conditional) must already be in the 
        list of proved WFFs or this rule will yield an error.

    Returns:
        A summary of the WFF added to the proof state.
    """
    C = require(conditional_id)

    if not in_proof(conditional_id):
        raise ValueError(f"Input conditional not in proof. "
                         f"WFF {str(conditional_id)} must be added as a premise "
                         f"or derived via an axiom or inference rule")

    if C.kind != "conditional":
        raise ValueError("Argument must be conditional")

    if not in_proof(C.left):
        raise ValueError(
            f"The antecedent of the conditional must be in the proof. "
            f"{str(C.left)} must be added as a premise "
            f"or derived via an axiom or inference rule")


    B_id = C.right
    B = require(B_id)

    new_id = store(WFF(
        id=0,
        kind=B.kind,
        value=B.value,
        left=B.left,
        right=B.right,
        child=B.child
    ))

    step = ProofStep(
        id=new_id,
        rule="modus_ponens",
        args=[C.left,conditional_id]
    )

    STATE.proof.append(step)

    return state_update(wff=STATE.wffs[new_id], proof_added=step)



@mcp.tool()
def adjunction(a_id: int, b_id: int):
    """
    A, B ⟹ (A AND B)

    Args:
        a_id: The id number for a conjunct.
        b_id: The id number for a conjunct.

    Requirements:

        a_id and b_id must already be in the list of
        proved WFFs or this rule will yield an error.

    Returns:
        A summary of the WFF added to the proof state.
    """

    A = require(a_id)
    B = require(b_id)

    if not in_proof(a_id):
        raise ValueError(f"A not in proof. "
                         f"{str(a_id)} must be added as a premise "
                        f"or derived via an axiom or inference rule")

    if not in_proof(b_id):
        raise ValueError(f"B not in proof. "
                         f"{str(b_id)} must be added as a premise "
                        f"or derived via an axiom or inference rule")
    new_id = store(WFF(
        id=0,
        kind="conjunction",
        value=None,
        left=a_id,
        right=b_id,
        child=None
    ))

    step = ProofStep(
        id=new_id,
        rule="adjunction",
        args=[a_id, b_id]
    )

    STATE.proof.append(step)

    return state_update(wff=STATE.wffs[new_id], proof_added=step)


# =========================
# Debug Helper
# =========================

@mcp.tool()
def debug_state():
    """Inspect full server state."""
    return render_state_view()

# =========================
# Entry
# =========================

if __name__ == "__main__":
    mcp.run()
