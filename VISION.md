# Product Vision

## The problem

Many coding agents assume access to powerful hardware, large context windows, paid APIs, or a permanently running local model. That excludes enthusiasts using ordinary laptops and desktops.

A second problem is context waste: repeatedly sending entire repositories or large documentation sets to a model is expensive and inefficient.

## The idea

NKK CodeMind is a **knowledge-on-demand coding system**.

The user describes an outcome. CodeMind inspects the current project, identifies missing technical knowledge, obtains reliable documentation when needed, retrieves only relevant information, selects an appropriate model/tool, performs the work, verifies it, and preserves useful knowledge for later.

The user can also supply documents, examples, API references, project conventions or requirements directly.

## Product principles

### 1. Knowledge is not model training

Adding documentation does not retrain the language model. Knowledge is stored separately and retrieved when needed. Fine-tuning, if ever introduced, is a separate optional research track.

### 2. Disk-first, RAM-light

Documents and indexes live on disk. Only relevant excerpts enter the active context. Models are loaded lazily, and runtime memory is measured rather than guessed.

### 3. Ask less, infer responsibly

Infer languages and frameworks from project files and task descriptions. Use sensible defaults. Ask a concise question only when ambiguity materially affects correctness, cost, privacy or destructive actions.

### 4. Model choice is a replaceable implementation detail

Use a small local model where it performs adequately. Escalate to an available cloud model for difficult work when configured and allowed. Never assume a free endpoint is always available.

### 5. Tools do deterministic work

Use file search, parsers, compilers, formatters, tests and Git for tasks they can perform more reliably than a language model.

### 6. Verify before claiming success

A successful model response is not proof that code works. Run applicable tests and report unverified items clearly.

## Target users

- Students and independent developers
- Open-source contributors
- Developers with CPU-only computers
- Enthusiasts who want to experiment with local and hosted models

## Initial hardware target

8 GB system RAM, CPU-only, Windows 10/11. This is an engineering target, not a performance guarantee. Actual support will be established through repeatable benchmarks on representative hardware.

## Non-goals for the first release

- Training a foundation model from scratch
- Automatically merging unrelated models
- Guaranteeing ChatGPT-level reasoning from tiny CPU models
- Running multiple large models simultaneously
- Unrestricted autonomous shell access
- Scraping websites without respecting access rules, licences or terms