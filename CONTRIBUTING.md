# Contributing

Contributions should remain small, inspectable, and evidence-first.

1. Open an issue or explain the intended gate in the pull request.
2. Add or update tests before changing the checker or contract schema.
3. Use synthetic fixtures only. Do not commit ODB, CAE, SIM, credentials, private manuscripts, or identifiable project data.
4. Document units, coordinate conventions, state names, and failure behavior.
5. Run `python -m unittest discover -s tests -v`, `git diff --check`, and the skill validator before requesting review.

Please keep each `SKILL.md` focused on a single decision boundary and keep frontmatter limited to the fields accepted by the Codex skill validator.
