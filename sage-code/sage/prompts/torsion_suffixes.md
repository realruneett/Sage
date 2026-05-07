# TORSION SUFFIXES LIBRARY

Select one suffix based on the perpendicular axis projection of the design vector:

1.  **Functional/Immutable**: "Constraint: Implement the solution using immutable data structures and pure functions. Avoid all class-level state and side effects. Prefer `namedtuple` or `dataclass(frozen=True)`."
2.  **Iterative/DP**: "Constraint: Avoid recursion. Implement the solution using iterative dynamic programming with explicit state management and manual memory optimization."
3.  **Data-Oriented**: "Constraint: Organize data into flat arrays/vectors. Minimize pointer chasing and deep object hierarchies to optimize for CPU cache locality and potential GPU offloading."
4.  **Async/Non-Blocking**: "Constraint: Every I/O operation must be non-blocking. Use `async`/`await` throughout. Implement explicit backpressure and timeout mechanisms."
5.  **Defensive/Hardened**: "Constraint: Implement aggressive input validation ('Parse, don't validate'). Every function must assume all inputs are malicious and handle malformed data without crashing."
6.  **Streaming/Lazy**: "Constraint: Optimize for memory by using generators and streaming. Do not materialize large collections in memory. Process data in chunks < 4KB."
7.  **Narrow Typing**: "Constraint: Use the narrowest possible type hints. Leverage `NewType`, `Literal`, and `Annotated` to encode business logic directly into the type system."
