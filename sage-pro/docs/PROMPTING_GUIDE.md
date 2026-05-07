# SAGE-PRO Prompting Guide

SAGE-PRO is not a simple chatbot; it is an adversarial reasoning engine. To get the best results, you should provide tasks that define high-level interfaces rather than low-level implementation details.

## Best Practices

1.  **Define Interfaces**: Clearly state expected inputs, outputs, and side effects.
2.  **State Constraints**: Use keywords like "thread-safe", "non-blocking", or "memory-efficient" to trigger the Torsion operators.
3.  **Provide Context**: Include relevant files using the `context_files` parameter to help the Router find topological voids.

## Examples

### ✅ Good: Task with Interface and Constraints
> "Implement a thread-safe LRU cache with TTL. The cache should support async eviction via a background worker. Key eviction should be O(1)."

### ❌ Bad: Task that is too vague
> "Write a cache script."

### ✅ Good: Complex System Refactoring
> "Refactor the existing database connection pool to use the Circuit Breaker pattern. Ensure it is robust against network timeouts."
