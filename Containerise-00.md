# Option One: Container Image Support for AWS Lambda

see https://www.serverless.com/blog/container-support-for-lambda

```
chrisbc@MLX01 nshm-hazard-graphql-api % aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 461564345538.dkr.ecr.us-east-1.amazonaws.com
Login Succeeded
```

## Get a base image

Let's use the AWS official python lambda image: `public.ecr.aws/lambda/python:3.12`

```
chrisbc@MLX01 nshm-hazard-graphql-api % docker pull public.ecr.aws/lambda/python:3.12
3.12: Pulling from lambda/python
7f6217391417: Pull complete
ef05d9f2265b: Pull complete
34328c8be51c: Pull complete
dc7934710945: Pull complete
287352861cd8: Pull complete
e480409eab85: Pull complete
Digest: sha256:594f15713623d599aa3d2cefe4e239e40ee90bf4182c07541b517acda04f0b3f
Status: Downloaded newer image for public.ecr.aws/lambda/python:3.12
public.ecr.aws/lambda/python:3.12
chrisbc@MLX01 nshm-hazard-graphql-api % docker image list
REPOSITORY                     TAG       IMAGE ID       CREATED       SIZE
public.ecr.aws/lambda/python   3.12      594f15713623   4 weeks ago   780MB
chrisbc@MLX01 nshm-hazard-graphql-api %
```

### get the requirements
poetry export --without-hashes --format=requirements.txt > requirements.txt

## A Dockerfile

see [Dockerfile](./Dockerfile)

```
#Dockerfile
FROM public.ecr.aws/lambda/python:3.12

ARG FUNCTION_DIR="/var/task"
 
# Create function directory
RUN mkdir -p ${FUNCTION_DIR}

COPY ./nshm_hazard_graphql_api ${FUNCTION_DIR}
COPY requirements.txt ${FUNCTION_DIR}

WORKDER ${FUNCTION_DIR}
RUN pip3 install -r requirements.txt

# lambda entry point
CMD ["nshm_hazard_graphql_api.app"]

ENTRYPOINT ["/bin/bash", "-c"]
```

### build it



