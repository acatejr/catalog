"""
Prompt library for the Catalog AI assistant.

Organized into three functional areas:
  - discovery    : Finding relevant datasets by topic or keyword
  - lineage      : Understanding data origin, provenance, and processing history
  - relationships: Discovering connections between datasets and systems

Each module provides a base system prompt plus persona-specific variants.
Persona modifiers are defined in personas.py and can be combined with any
functional prompt using build_system_prompt().

Supported personas:
  - ANALYST    : USFS GIS analyst (technical depth)
  - FORESTER   : USFS field forester (operational focus)
  - MANAGER    : USFS managerial staff (executive summaries)
  - PUBLIC     : General public (plain language)
  - POLITICIAN : Elected officials (policy and impact)

Example usage::

    from catalog.prompts import build_system_prompt, Persona
    from catalog.prompts.lineage import LINEAGE_PROMPTS

    system_prompt = build_system_prompt(
        functional_prompt=LINEAGE_PROMPTS[Persona.PUBLIC],
        persona=Persona.PUBLIC,
    )
"""

from catalog.prompts.personas import Persona, PERSONA_MODIFIERS


def build_system_prompt(functional_prompt: str, persona: Persona) -> str:
    """
    Combine a functional system prompt with a persona modifier.

    :param functional_prompt: The task-specific system prompt (discovery, lineage, etc.)
    :param persona: The target user persona.
    :return: A complete system prompt string ready to send to any LLM.
    """
    modifier = PERSONA_MODIFIERS[persona]
    return f"{functional_prompt}\n\n---\n\n{modifier}"


__all__ = ["Persona", "PERSONA_MODIFIERS", "build_system_prompt"]
