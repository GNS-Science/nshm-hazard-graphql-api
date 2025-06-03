#Dockerfile
FROM public.ecr.aws/lambda/python:3.11

ARG FUNCTION_ROOT_DIR="/var/task"
 
# Create function directory
RUN mkdir -p ${FUNCTION_ROOT_DIR}/nshm_hazard_graphql_api


COPY ./nshm_hazard_graphql_api/ ${FUNCTION_ROOT_DIR}/nshm_hazard_graphql_api

COPY pyproject.toml ${FUNCTION_ROOT_DIR}
COPY poetry.lock ${FUNCTION_ROOT_DIR}
COPY README.md ${FUNCTION_ROOT_DIR}

# COPY requirements.txt ${FUNCTION_DIR}
RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR ${FUNCTION_ROOT_DIR}

RUN ${HOME}/.local/bin/poetry install
# RUN pip3 install -r requirements.txt

# lambda entry point
CMD ["nshm_hazard_graphql_api.nshm_hazard_graphql_api.app"]
ENTRYPOINT ["/bin/bash", "-c"]