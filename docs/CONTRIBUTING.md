# Contributing to NULL

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a feature branch from `main`

## Branch Strategy

| Branch | Purpose |
|---|---|
| `main` | Stable release branch |
| `dev` | Active development branch |
| `feature/*` | New features |
| `fix/*` | Bug fixes |
| `docs/*` | Documentation updates |

## Commit Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]
```

**Types:**
- `feat` — New feature
- `fix` — Bug fix
- `docs` — Documentation changes
- `refactor` — Code refactoring
- `test` — Adding or updating tests
- `chore` — Maintenance tasks

**Examples:**
```
feat(genesis): implement seed prompt parser
fix(hivemind): resolve wiki page duplication
docs(readme): update roadmap section
```

## Pull Request Process

1. Ensure your branch is up to date with `main`
2. Write clear PR title and description
3. Link related issues
4. Request review from at least one maintainer
5. All CI checks must pass before merge

## Code Standards

- Python: Follow PEP 8, use type hints
- TypeScript: Follow ESLint configuration
- All functions must have docstrings/JSDoc
- Tests required for new features

## Documentation

- All docs maintain English + Korean (`.ko.md`) versions
- Update both versions when making documentation changes
- Keep the glossary up to date with new terms

## Questions?

Open an issue with the `question` label.
