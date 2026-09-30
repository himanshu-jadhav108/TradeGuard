# Deployment

Recommended split:
- Next.js frontend: Vercel or equivalent.
- FastAPI backend: Render/Railway/Fly/etc. depending on current free-tier availability and hackathon constraints.

If SQLite is used in a hosted environment, understand that ephemeral disks may lose state. For the demo, use seeded/demo state or a persistent managed DB if required.

Production secrets belong in the hosting provider's secret manager.

Deployment acceptance:
- HTTPS
- health endpoint
- CORS restricted to frontend origin
- no credentials in client
- DEMO works without external secrets
- UAT works only when configured
