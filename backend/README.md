# Selflytics Backend

FastAPI backend for Selflytics - AI-powered analysis for quantified self data.

## Project Structure

```
backend/
├── app/
│   ├── auth/          # JWT authentication, password hashing
│   ├── db/            # Database clients (Firestore)
│   ├── middleware/    # FastAPI middleware
│   ├── models/        # Pydantic models
│   ├── routes/        # API endpoints
│   ├── services/      # Business logic
│   ├── templates/     # Jinja2 templates
│   ├── prompts/       # AI agent system prompts
│   └── utils/         # Utility functions
├── packages/
│   └── telemetry/     # Workspace package for telemetry
└── tests/
    ├── unit/          # Unit tests
    ├── integration/   # Integration tests
    └── e2e/           # End-to-end tests
```

## Quick Start

See project root README.md for complete setup instructions.
