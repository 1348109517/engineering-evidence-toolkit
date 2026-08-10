# Security and data boundary

This repository is for public, clean-room workflow material. Never commit API keys, passwords, cookies, private email, proprietary geometry, ODB/CAE/SIM databases, or unpublished manuscript files.

If a sensitive file is found in an unpushed local change, remove it before committing and rotate any exposed credential. If sensitive material has already reached a public commit, treat it as exposed: revoke or rotate it, then contact the repository maintainer with the commit and file path. Do not paste secrets into an issue.

The checker validates metadata and references; it does not sandbox arbitrary JSON or execute project commands.
