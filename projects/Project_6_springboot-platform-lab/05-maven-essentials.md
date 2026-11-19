---
layout: default
title: "Block 5: Maven essentials"
parent: 8. Spring Boot Platform Lab
nav_order: 8
---

# Block 5: Maven essentials

**Status:** Not started

## Goal

Know enough Maven to support Java teams in CI: lifecycle, dependency problems, repositories and reproducible builds.

## Reference

| Topic | Know this |
|---|---|
| Lifecycle | `validate`, `compile`, `test`, `package`, `verify`, `install`, `deploy` |
| `verify` vs `package` | `verify` also runs integration tests and quality checks |
| Dependency problems | `mvn dependency:tree -Dverbose` finds conflicts, `-U` forces snapshot update |
| SNAPSHOT vs release | SNAPSHOTs are mutable and for development; releases are immutable |
| `settings.xml` | Mirrors (point to Artifactory), server credentials (injected from CI secrets), profiles |
| `mvn deploy` | Publishes to a repository via `distributionManagement` |
| CI flags | `-B` batch mode, `-ntp` no transfer progress |
| Reproducibility | Pinned versions, parent POM or BOM, Maven wrapper |

Artifactory mirror:

```xml
<mirror>
  <id>artifactory</id>
  <mirrorOf>*</mirrorOf>
  <url>https://artifactory.company.com/artifactory/maven-virtual</url>
</mirror>
```

## Exercises

1. Run `mvn dependency:tree` on the demo project and note the direct dependencies.
2. Add a conflicting dependency version and find it with `-Dverbose`.
3. Run `mvn -B -ntp verify` and read the phases in the output.
4. Compare build time with and without the CI Maven cache.

## Results

```
<paste outputs>
```

## Next

[Block 6: Interview Q&A](06-interview-qa)
