"""
This module exports comfiguration for the current system
"""
import os

from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env


def boolean_env(environ_name, default='FALSE'):
    return bool(os.getenv(environ_name, default).upper() in ["1", "Y", "YES", "TRUE"])


IS_OFFLINE = boolean_env('SLS_OFFLINE')  # set by serverless-wsgi plugin

REGION = os.getenv('REGION', 'ap-southeast-2')
DEPLOYMENT_STAGE = os.getenv('DEPLOYMENT_STAGE', 'LOCAL').upper()
STACK_NAME = os.getenv('STACK_NAME', 'nshm_hazard_graphql_api')

LOGGING_CFG = os.getenv('LOGGING_CFG', 'nshm_hazard_graphql_api/logging_aws.yaml')
ENABLE_METRICS = bool(os.getenv('ENABLE_METRICS', '').upper() in ["1", "Y", "YES", "TRUE"])
CW_METRICS_RESOLUTION = os.getenv('CW_METRICS_RESOLUTION', 60)  # 1 for high resolution or 60

DATASET_AGGR_ENABLED = bool(os.getenv('DATASET_AGGR_ENABLED', '').upper() in ["1", "Y", "YES", "TRUE"])
DATASET_AGGR_URI = os.getenv('DATASET_AGGR_URI', '')
