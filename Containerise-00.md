# Option One: Container Image Support for AWS Lambda

see https://www.serverless.com/blog/container-support-for-lambda



## login to aws ecr

```
chrisbc@MLX01 nshm-hazard-graphql-api % aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 461564345538.dkr.ecr.us-east-1.amazonaws.com

chrisbc@MLX01 nshm-hazard-graphql-api % aws ecr get-login-password --region ap-southeast-2 | docker login --username AWS --password-stdin 461564345538.dkr.ecr.ap-southeast-2.amazonaws.com
Login Succeeded
```

## Get a base image

Using the AWS official python lambda image: `public.ecr.aws/lambda/python:3.11`

```
docker pull public.ecr.aws/lambda/python:3.11
3.12: Pulling from lambda/python
.....
Status: Downloaded newer image for public.ecr.aws/lambda/python:3.11
public.ecr.aws/lambda/python:3.11
```

### get the requirements
poetry export --without-hashes --format=requirements.txt > requirements.txt

### test wsgi handlers

`poetry run npx serverless wsgi serve`

## A Dockerfile

see [Dockerfile](./Dockerfile)

### build it

`BUILDX_NO_DEFAULT_ATTESTATIONS=1 npx serverless package`

### and/or deploy it

this will push the image

`BUILDX_NO_DEFAULT_ATTESTATIONS=1 npx serverless deploy  --stage dev --region us-east-1`