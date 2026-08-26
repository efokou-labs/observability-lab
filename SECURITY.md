# Security policy

## Reporting a vulnerability

Do not open a public issue for security reports.

Email the maintainer via the GitHub profile listed on this organization/account,
or use GitHub's private vulnerability reporting on the affected repository.

## Rules for this portfolio

- Never commit secrets, private keys, kubeconfigs, or `.env` files.
- Authenticate GitHub Actions to AWS with OIDC only. Long-lived access keys are not used.
- Default compute target is local kind. AWS resources are ephemeral: apply, demo, destroy.
- Put a $10 AWS budget alarm in any account used for this portfolio before the first `apply`.
- Container images are scanned with Trivy in CI before they are considered releasable.
