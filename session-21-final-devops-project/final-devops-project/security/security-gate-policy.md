# Security gate policy (used by job "8. Security Gate" in the workflow)

| Check | Tool | Blocks the pipeline when |
|---|---|---|
| SAST | CodeQL (python + javascript) | 1 or more findings |
| SCA | pip-audit (backend) + npm audit (frontend) | 1 or more known vulnerable dependencies |
| Secret scanning | Gitleaks | 1 or more secrets in the project files |
| Image scanning | Trivy | 1 or more HIGH / CRITICAL CVEs in the backend or frontend image |
| Any scan job | - | the scan job itself did not finish with `success` |

If the gate fails, "9. Push Image", "10. Deploy" and "11. GitOps update" are skipped,
so a vulnerable image never reaches the registry or the cluster.
