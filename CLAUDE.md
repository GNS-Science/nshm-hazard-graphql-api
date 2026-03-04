# CLAUDE.md - Project Context for AI Assistants

This file provides project-specific context for AI assistants working on this codebase.

## Project Overview

- **Name**: nshm-hazard-graphql-api
- **Type**: GraphQL API (Flask + Graphene, deployed via Serverless Framework on AWS Lambda)
- **Python**: Requires Python >=3.12, <3.13
- **Node**: Requires Node >=22 (for Serverless Framework tooling)
- **Package Manager**: Yarn Berry (v4) with `node-modules` linker

## Development Commands

### Environment Setup
```bash
# Python
pyenv local 3.12
poetry env use 3.12
poetry install

# Node/Yarn
corepack enable
yarn set version berry
yarn install
```

### Testing
```bash
poetry run pytest
```

### Run API Locally
```bash
ENABLE_METRICS=0 poetry run yarn sls wsgi serve
```

### Format & Lint
```bash
poetry run black nshm_hazard_graphql_api tests
poetry run isort nshm_hazard_graphql_api tests
poetry run flake8 nshm_hazard_graphql_api tests
```

## Key Architecture

- **Framework**: Flask + Graphene (GraphQL)
- **Deployment**: AWS Lambda via Serverless Framework (containerised via Dockerfile)
- **Data source**: toshi-hazard-store (PyArrow parquet datasets on S3)
- **WSGI**: serverless-wsgi plugin bridges Lambda events to Flask

## Yarn Berry Configuration

This project uses Yarn Berry (v4) with `nodeLinker: node-modules` (set in `.yarnrc.yml`).

**Important**: The `node-modules` linker is required because `serverless-wsgi` needs filesystem
access to `serve.py` for local development (`sls wsgi serve`). Yarn Berry's default PnP mode
stores packages in zip archives, which Python cannot execute directly.

If `.yarnrc.yml` is missing or doesn't contain `nodeLinker: node-modules`, the local dev server
will fail with:
```
can't find '__main__' module in '.../.yarn/berry/cache/serverless-wsgi-npm-*.zip/...'
```

## Important Files

- `serverless.yml` - Serverless Framework configuration (Lambda, API Gateway, IAM)
- `pyproject.toml` - Python project configuration and dependencies
- `package.json` - Node dependencies (serverless plugins)
- `.yarnrc.yml` - Yarn Berry config (must use `nodeLinker: node-modules`)
- `nshm_hazard_graphql_api/` - Application source code
- `Dockerfile` - Container image for Lambda deployment
- `tests/` - Pytest tests

## Key Dependencies

- **toshi-hazard-store**: Hazard data query library (parquet datasets)
- **nzshm-model**: NZSHM model definitions
- **nzshm-common**: Shared utilities (location grids, etc.)
- **graphene**: GraphQL schema library
- **flask**: WSGI web framework
- **serverless-wsgi**: Bridges Flask to AWS Lambda
