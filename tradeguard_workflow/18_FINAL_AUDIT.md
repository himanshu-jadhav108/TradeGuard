# Final Audit Prompt

Before declaring completion:
- inspect git diff
- inspect dependency tree
- run lint
- run typecheck
- run backend tests
- run frontend tests
- run E2E
- run production build
- search for TODO/FIXME in critical paths
- search for secrets/key files
- verify no True Markets calls exist in frontend
- verify demo mode
- verify theme toggle
- verify mobile layout
- verify error states
- verify order confirmation gate
- verify UAT integration if credentials exist
- produce a concise final audit with pass/fail and remaining issues
