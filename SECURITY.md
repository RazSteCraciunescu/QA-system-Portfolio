# Security policy

RelayHub is a synthetic test environment. Do not expose the partner-simulator administration endpoints to an untrusted network.

## Supported branch

Security fixes are applied to `main`.

## Reporting a problem

Do not place credentials, access tokens, personal data, customer data, or exploit material in a public issue. Provide a minimal reproduction using synthetic data and describe:

- affected component and version;
- impact and reachable attack path;
- prerequisites;
- proof using non-sensitive test data;
- suggested containment, when known.

## Local environment rules

- Keep `.env` untracked.
- Replace the sample partner administration token outside localhost.
- Bind diagnostic service ports to `127.0.0.1` unless remote access is explicitly required.
- Treat generated logs and evidence as controlled test artefacts until reviewed.
- Do not copy production payloads into `test-data/`.
