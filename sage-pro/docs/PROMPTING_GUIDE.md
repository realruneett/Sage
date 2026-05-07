# SAGE-CODE Prompting Guide

## The Specialist Agents

SAGE-CODE uses four specialized agents to ensure high-fidelity code generation.

### ARCHITECT
Focus: Layout, interfaces, and contracts.
Input: User requirement.
Output: Design doc + Mermaid diagrams.

### IMPLEMENTER
Focus: Idiomatic code.
Input: Design doc + Torsion Nudge.
Output: Python implementation.

### SYNTHESIZER
Focus: Refinement and conflict resolution.
Input: Two candidate implementations + Red-Team findings.
Output: Merged, defensive code.

### RED-TEAM
Focus: Breaking things.
Input: Candidate code.
Output: Pytest cases + security findings.

## Torsion Nudges

To explore the solution manifold, use the `TorsionGenerator` to inject orthogonal constraints. This prevents the system from converging on a sub-optimal "vanilla" solution.
