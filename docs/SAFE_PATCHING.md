# Safe Patch Application

CodeMind can validate and preview a unified diff before applying it to a project.

## Preview first

```powershell
python -m codemind apply-patch .\change.patch --workspace .\my-project
```

The command prints the exact diff and leaves the project unchanged.

## Apply after review

```powershell
python -m codemind apply-patch .\change.patch --workspace .\my-project --apply
```

CodeMind validates the patch again and checks that each target file has not changed since preview. It writes each changed file through a temporary file and atomic replacement. If a later write fails, it attempts to restore files already written by that operation.

## Current safety boundaries

- Existing UTF-8 text files only; creating, deleting and renaming files are rejected.
- Maximum patch size: 2 MB.
- Maximum files per patch: 20.
- Maximum target file size: 1 MB.
- Absolute paths, parent-directory traversal and symlink targets are rejected.
- Every hunk must match the current file content exactly.
- Duplicate target paths and overlapping/out-of-range hunks are rejected.
- Preview is the default. Writing requires the explicit `--apply` flag.
- This command does not run shell commands, tests or formatters.
- The `ask --workspace` command still supplies read-only context; it does not autonomously generate or apply patches.

## Next steps

1. Add a Git-aware diff and user-controlled rollback view.
2. Let the model propose a patch in a structured, bounded format.
3. Require user approval before applying model-generated changes.
4. Add command allowlists and explicit per-project test/formatter permissions.
5. Build the bounded inspect → plan → edit → test → repair → verify loop.
