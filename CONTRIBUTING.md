# Contributing to review-service

This service is owned by the **Social & Reviews** team. All changes go through PR review by at least one team member.

## Development Workflow

1. Create a feature branch from `main`.
2. Make your changes and add tests where applicable.
3. Run the service locally and verify your changes with the curl examples in the README.
4. Open a PR with a clear description of what changed and why.

## Code Style

- Follow PEP 8.
- Use `logging` instead of `print` statements.
- Keep endpoint handlers focused; extract business logic into helper functions when complexity grows.

## Testing

Run tests with:

```bash
python -m pytest test_app.py -v
```

## Known Issues

The following are tracked and will be addressed in upcoming sprints:

- **Input validation:** The `POST /api/v1/reviews` endpoint does not enforce rating range (1-5) or input length limits on title/body fields.
- **Sanitization:** User-submitted review text is stored and returned without HTML sanitization. This must be resolved before any server-side rendering is introduced.

If you encounter additional issues, file a ticket in Linear under the `social-reviews` project.
