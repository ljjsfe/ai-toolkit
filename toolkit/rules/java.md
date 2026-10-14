---
paths:
  - "**/*.java"
  - "**/*.kt"
  - "**/pom.xml"
  - "**/build.gradle*"
---
# Java / Spring traps

- Spring Boot 3 / Spring Security 6: `WebSecurityConfigurerAdapter` is **removed**. Use a
  `SecurityFilterChain` `@Bean` with the lambda DSL.
- Boot 3 uses `jakarta.*`, not `javax.*`, for servlet, persistence and validation. A leftover
  `javax` import may still compile when an old jar is on the classpath — and the annotation is
  then silently ignored.
- JPA `@ManyToOne` and `@OneToOne` are **EAGER by default**; set `fetch = FetchType.LAZY`
  explicitly. Two `JOIN FETCH` on different bag collections throw `MultipleBagFetchException`;
  use `@BatchSize` or separate queries.
- Never call `.block()` inside a WebFlux reactive chain; it stalls the event loop.
- `@Transactional` on a method called from the same class does nothing (proxy bypass); move it
  to another bean or call through the proxy.
