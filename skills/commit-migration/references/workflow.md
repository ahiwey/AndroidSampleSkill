# Workflow

## Intent parsing

Convert the user's request into one of these selector types:

- single commit
- multiple commits
- range `A..B`
- branch diff
- recent commits from a branch
- local source repository plus explicit file set

Reject ambiguous placeholder patterns such as:

- `459591xx`
- `A~B`

## Safe workflow

1. Identify the target repository and current branch.
2. Confirm the request is about applying changes into the current branch.
3. Analyze the source selection.
4. Snapshot target dirty files and load repository mapping hints.
5. Review the mapping output, protected/merge-only paths, and resource gaps before editing files.
6. For long files, use fingerprinted slices instead of whole-file terminal output.
7. Port the equivalent behavior into the current branch.
8. Validate with static checks, compile, focused tests, then assemble when resources or wiring changed.
9. Check Android follow-up items.
10. Summarize what was ported and what still needs human attention.

## What not to do automatically

- do not modify the source branch
- do not switch branches without explicit permission
- do not blindly apply `cherry-pick`
- do not overwrite current-branch custom logic when the repository clearly diverged
- do not select a protected path through filename similarity
- do not print source files over 400 lines as one compacted terminal result
