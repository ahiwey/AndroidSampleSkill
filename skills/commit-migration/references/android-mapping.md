# Android Mapping Strategy

## File mapping order

Use this order when trying to find the current-branch destination:

1. explicit path overrides from mapping hints
2. related target hosts, layouts, and helpers from mapping hints
3. package-root replacement
4. exact same file name under code roots
5. same responsibility inferred from neighboring directory structure
6. ask for confirmation only when the mapping is genuinely risky

## Resource mapping

Look for both:

- file resources under `res/<type>/`
- values resources defined inside `values/*.xml`

Treat an exact `values.xml#resource_name` match as a direct candidate.

## Class and reference adaptation

When code changes touch Android components, remember that references may appear outside the source file:

- manifest class names
- layout custom view names
- navigation destinations
- providers and authorities
- reflection strings
- route constants
- serialization names
- R8 or Proguard rules

## Multi-brand repository behavior

In multi-brand Android repositories, prefer preserving the target branch's existing:

- naming conventions
- directory structure
- resource naming
- branch-specific business logic

The goal is not to replay the source branch literally. The goal is to preserve the source behavior in the target repository's existing structure.

Use `related_paths` when one source component affects a differently named host, shared layout, helper, or policy file. This makes preservation requirements and dirty-file collisions visible even when the direct file mapping is unambiguous.
