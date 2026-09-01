# Contributing

This repository is organized for five developers working concurrently. Respect the ownership boundaries below and coordinate before editing another developer's paths.

| Owner | Paths |
| --- | --- |
| Developer 1 | `backend/app/api/**`, `backend/app/core/**`, `backend/app/db/**`, `backend/app/services/orchestrator/**`, `backend/app/services/reporting/**` |
| Developer 2 | `backend/app/services/email_forensics/**`, `backend/tests/email_forensics/**`, `fixtures/emails/**` |
| Developer 3 | `backend/app/services/detection/**`, `backend/app/services/risk/**`, `backend/tests/detection/**`, `backend/tests/risk/**` |
| Developer 4 | `backend/app/services/threat_intel/**`, `backend/app/services/geolocation/**`, `backend/tests/threat_intel/**`, `backend/tests/geolocation/**` |
| Developer 5 | `frontend/**` |

`backend/app/schemas/**`, `docs/contracts/**`, root documentation, and configuration examples are shared contracts. Changes to them require team review because they can affect every workstream.

## Contract-first workflow

1. Propose shared schema and endpoint changes before implementation.
2. Keep service implementations behind the interfaces in each service package.
3. Add tests only in the owning test directory; integration/API tests belong in their named shared directories.
4. Run `ruff` and `pytest` once project configuration and dependencies are added by the team.
5. Never commit secrets, live evidence, uploaded messages, generated reports, or local databases.

## Security invariants

- Treat every email, header, body, attachment name, and extracted indicator as hostile data.
- Never treat email content as instructions to an AI system or application runtime.
- Never execute attachments or automatically visit extracted URLs.
- Never render untrusted HTML. A future UI must sanitize into a separate derived representation or display it as escaped text.
- Use generated storage identifiers and a fixed evidence root; never derive file paths from user-supplied names.
- Validate media type, extension, size, and message structure at the upload boundary.
- Read provider credentials only from environment variables, redact them from errors, and never log them.
- Convert provider failures and absent reputation into `UNKNOWN`; absence of evidence is not a `BENIGN` verdict.

## Pull requests

Keep changes scoped to one owner's paths when possible. Call out shared-contract changes, migrations, new dependencies, external network behavior, and security-impacting decisions in the pull request description.

