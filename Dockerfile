#Dockerfile
FROM public.ecr.aws/lambda/python:3.11

ARG FUNCTION_ROOT_DIR="/var/task"
 
# Create function directory
RUN mkdir -p ${FUNCTION_ROOT_DIR}/nshm_hazard_graphql_api

# The lamba service functions
COPY ./nshm_hazard_graphql_api/ ${FUNCTION_ROOT_DIR}/nshm_hazard_graphql_api
COPY requirements.txt ${FUNCTION_DIR}

WORKDIR ${FUNCTION_ROOT_DIR}

RUN pip3 install -r requirements.txt

# lambda entry point
CMD ["nshm_hazard_graphql_api.nshm_hazard_graphql_api.app"]
ENTRYPOINT ["/bin/bash", "-c"]
