#Dockerfile
FROM public.ecr.aws/lambda/python:3.13

ARG FUNCTION_ROOT_DIR="/var/task"

# Create function directory
RUN mkdir -p ${FUNCTION_ROOT_DIR}/nshm_hazard_graphql_api

# The lamba service functions
COPY ./nshm_hazard_graphql_api/ ${FUNCTION_ROOT_DIR}/nshm_hazard_graphql_api
COPY requirements.txt ${FUNCTION_ROOT_DIR}
WORKDIR ${FUNCTION_ROOT_DIR}
# add gcc because some packages might need to be built (contourpy)
# add git to be able to install NZSHM libraries from git
RUN dnf install git-core gcc gcc-c++ -y &&\
    pip install --upgrade pip &&\
    pip3 install --no-deps -r requirements.txt &&\
    pip cache purge &&\
    dnf clean all

# lambda entry point
CMD ["nshm_hazard_graphql_api.nshm_hazard_graphql_api.app"]
ENTRYPOINT ["/bin/bash", "-c"]
