# DEVELOPMENT

This application uses serverless.com.

## Environment setup

- Clone the repo
- Check/install a recent node version >=22:
  `nvm use 22`

- Setup python env:

```bash
pyenv local 3.12
uv python pin 3.12
uv sync
```

- Setup Yarn Berry (node-modules linker is required for serverless-wsgi local dev):

```bash
corepack enable
yarn set version berry
yarn install
```

Now `yarn sls info` should print something like:

```
Running "serverless" from node_modules
Environment: linux, node 22.x.x, framework 4.x.x (local) ...
```

You'll probably see an error if your AWS credentials are not those required for SLS.

## Configuration

Create a `.env` file in the project root (see `.env` for an example). The key variables are:

### Required

| Variable | Description | Example |
|----------|-------------|---------|
| `THS_DATASET_AGGR_URI` | S3 URI for aggregated hazard curves dataset | `s3://ths-dataset-prod/NZSHM22_AGG` |
| `THS_DATASET_GRIDDED_URI` | S3 URI for gridded hazard dataset | `s3://ths-dataset-prod/NZSHM22_GRIDDED` |
| `THS_DATASET_AGGR_ENABLED` | Enable aggregated dataset features | `True` |
| `AWS_PROFILE` | AWS credentials profile for S3 access | `chrisbc` |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `NZSHM22_HAZARD_STORE_STAGE` | `LOCAL` | Deployment stage (e.g. `PROD`, `TEST`) |
| `NZSHM22_HAZARD_STORE_REGION` | `us-east-1` | AWS region for hazard store |
| `ENABLE_METRICS` | `True` | Enable CloudWatch metrics |
| `COLOR_SCALE_NORMALISATION` | `LIN` | Colour scale normalisation (`LIN` or `LOG`) |

### Example `.env`

```bash
NZSHM22_HAZARD_STORE_STAGE=PROD
NZSHM22_HAZARD_STORE_REGION=ap-southeast-2
AWS_PROFILE=your-profile-name

THS_DATASET_AGGR_ENABLED=True
THS_DATASET_AGGR_URI=s3://ths-dataset-prod/NZSHM22_AGG
THS_DATASET_GRIDDED_URI=s3://ths-dataset-prod/NZSHM22_GRIDDED

ENABLE_METRICS=0
```

## AWS credentials

Contact nshm@gns.cri.nz for read-only AWS credentials to access the NSHM datasets.

Short-term credentials should be configured as a named profile in `~/.aws/credentials`. See
[AWS short-term credentials](https://docs.aws.amazon.com/cli/v1/userguide/cli-authentication-short-term.html).

## Testing

### API feature tests

```bash
uv run pytest
```

### Run API locally

```bash
ENABLE_METRICS=0 uv run yarn sls wsgi serve
```
