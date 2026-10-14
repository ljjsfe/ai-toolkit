---
paths:
  - "**/*.cpp"
  - "**/*.cc"
  - "**/*.cxx"
  - "**/*.h"
  - "**/*.hpp"
  - "**/CMakeLists.txt"
---
# C++ traps

- A lambda that captures locals by reference must not outlive them: never pass `[&]` lambdas to
  detached threads, async callbacks or stored handlers.
- An unnamed guard is a temporary that unlocks at the end of the statement:
  `std::lock_guard<std::mutex>{m};` or `std::scoped_lock{m};` protect nothing. Always name it:
  `std::lock_guard lock(m);` (Writing `std::lock_guard<std::mutex>(m);` declares a new
  variable `m` and fails to compile.)
- Never return a reference or pointer to a local. Do not declare return types `const T` — it
  disables moves.
- Ranges views are lazy and reference their source. Piping an rvalue container is safe (it
  becomes an owning view), but a view over a member of a temporary, or over a borrowed
  temporary such as a `std::string_view` of a destroyed string, dangles.
- Coroutines: a reference parameter dangles after the first `co_await` if the caller passed a
  temporary; take by value. Types owning a coroutine handle need the full rule of five.
- Atomics: do not use `memory_order_relaxed` where another thread must see related writes;
  pair `release` with `acquire`. Lock-free structures need safe memory reclamation (hazard
  pointers or epochs) — a CAS loop followed by `delete` is use-after-free.
- Custom allocators must satisfy the allocator requirements (`rebind`, equality).
