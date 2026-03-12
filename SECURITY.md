# Security Policy

## Reporting a Vulnerability

If you identify a security issue, do not open a public issue with exploit details.

Use one of the following channels:
- GitHub private security advisory (preferred)
- Direct contact with repository owner

Include:
- Affected component/file
- Reproduction steps
- Potential impact
- Suggested mitigation (if available)

## Supported Scope

Security reports are accepted for:
- Application code in `app/` and `src/`
- Dependency configuration files
- CI workflow definitions

## Operational Safeguards

- Upload limits are enforced through environment-backed settings: `MAX_UPLOAD_MB`, `MAX_UPLOAD_ROWS`, and `MAX_UPLOAD_COLUMNS`.
- CSV uploads are parsed defensively with delimiter/encoding detection and invalid-line skipping.
- The dashboard rejects oversized or malformed uploads before analysis starts.
