# Selflytics

**AI-powered analysis and insights for quantified self data from wearable devices**

[![CI](https://github.com/beldaz/selflytics/workflows/CI/badge.svg)](https://github.com/beldaz/selflytics/actions)
[![Coverage](https://codecov.io/gh/beldaz/selflytics/branch/main/graph/badge.svg)](https://codecov.io/gh/beldaz/selflytics)

## Overview

Selflytics provides natural language chat interface for exploring personal fitness data with AI-generated visualizations and personalized insights. Built with privacy-first principles, it enables non-technical users to gain actionable insights from their wearable device data.

**Current Status:** 🚧 In Development - Initial Specification Phase

## Features (Planned)

- 🤖 **Natural Language Chat** - Ask questions about your fitness data in plain English
- 📊 **AI-Generated Visualizations** - Dynamic charts created on-demand
- 🏃 **Garmin Integration** - Secure OAuth connection to Garmin Connect
- 🎯 **Goal Tracking** - Set and monitor fitness goals with AI insights
- 🔒 **Privacy-First** - Your health data stays secure and private

## Technology Stack

- **Backend:** FastAPI + Python 3.12+ (uv package manager)
- **AI Framework:** Pydantic-AI with OpenAI gpt-4.1-mini
- **Frontend:** Jinja2 + HTMX + Alpine.js + TailwindCSS
- **Infrastructure:** GCP Cloud Run + Firestore + Terraform
- **Garmin Integration:** garth library
- **Telemetry:** OpenTelemetry + Cloud Logging

## Project Structure

```
selflytics/
├── backend/          # FastAPI application
├── infra/            # Terraform infrastructure
├── docs/             # Documentation
├── static/           # Frontend assets
└── scripts/          # Utility scripts
```

## Documentation

- [Full Specification](/docs/SELFLYTICS_SPECIFICATION.md) - Complete technical specification
- [Garmin Agents Exploration](/docs/GARMIN_AGENTS_EXPLORATION.md) - Reference implementation analysis
- [Reusable Patterns Guide](/docs/REUSABLE_PATTERNS_GUIDE.md) - Design patterns and best practices

## Development Roadmap

### Current Phase: Spike (Week 1)
- [ ] Pydantic-AI chat agent prototype
- [ ] Garmin integration proof-of-concept
- [ ] Visualization generation validation

### Upcoming Phases
1. **Phase 1:** Infrastructure Foundation (2 weeks)
2. **Phase 2:** Garmin Integration (2 weeks)
3. **Phase 3:** Chat Interface + AI Agent (3 weeks)
4. **Phase 4:** Visualization Generation (2 weeks)
5. **Phase 5:** Goals & Polish (1 week)
6. **Phase 6:** Launch Preparation (1 week)

**Total Estimated Duration:** 12 weeks

## Getting Started

> 📝 **Note:** Detailed setup instructions will be added as the project develops.

### Prerequisites

- Python 3.12+
- uv package manager
- GCP account (for deployment)
- Garmin Connect account

### Local Development

```bash
# Clone the repository
git clone https://github.com/beldaz/selflytics.git
cd selflytics

# Setup will be documented as implementation progresses
```

## Contributing

This is currently a personal project. Contribution guidelines will be established once the MVP is complete.

## License

To be determined

## Acknowledgments

Built upon learnings from:
- **Garmin Agents** - Garmin integration patterns and AI agent design
- **CliniCraft** - Infrastructure, CI/CD, and frontend architecture

---

**Author:** beldaz
**Production URL:** https://selflytics.anbaricideas.com (coming soon)
**Status:** Pre-alpha - Active Development
