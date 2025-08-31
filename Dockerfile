#Dockerfile
FROM public.ecr.aws/lambda/python:3.13

ARG FUNCTION_ROOT_DIR="/var/task"
 
# # GIT
# RUN dnf install  -y

# Create function directory
RUN mkdir -p ${FUNCTION_ROOT_DIR}/nshm_hazard_graphql_api

# The lamba service functions
COPY ./nshm_hazard_graphql_api/ ${FUNCTION_ROOT_DIR}/nshm_hazard_graphql_api
COPY requirements.txt ${FUNCTION_ROOT_DIR}
WORKDIR ${FUNCTION_ROOT_DIR}
# #some packages might need to be built (contourpy)
RUN dnf install git-core gcc gcc-c++ -y &&\
    pip install --upgrade pip &&\
    pip3 install --no-deps -r requirements.txt &&\
    pip cache purge &&\
    dnf clean all

# #pyproj requires proj
# RUN yum repolist
# #RUN cat /etc/yum.conf
# #RUN ls -lath /etc/yum.repos.d
# RUN amazon-linux-extras install epel -y
# RUN dnf config-manager --dump

# # RUN yum repoinfo rhel-7-server-rpms
# # RUN yum search proj
# RUN yum update -y && \
#     yum install proj -y


# RUN pip install --upgrade pip
# RUN pip3 install --no-deps -r requirements.txt

# lambda entry point
CMD ["nshm_hazard_graphql_api.nshm_hazard_graphql_api.app"]
ENTRYPOINT ["/bin/bash", "-c"]
