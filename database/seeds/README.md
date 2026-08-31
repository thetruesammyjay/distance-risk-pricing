# Development seeds

Seed data must be labelled development-only, simulated, or synthetic. Never
represent seed records as empirical research observations.

Apply migrations before seeding:

```powershell
uv run alembic upgrade head
uv run python -m scripts.seed_database
```

The seed command is idempotent and refuses `APP_ENV=production` unless
`--allow-synthetic` is provided. Prefer a Neon staging branch for demo data.
