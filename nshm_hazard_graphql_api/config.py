"""
This module exports comfiguration for the current system
"""
import os


def boolean_env(environ_name, default='FALSE'):
    return bool(os.getenv(environ_name, default).upper() in ["1", "Y", "YES", "TRUE"])


IS_OFFLINE = boolean_env('SLS_OFFLINE')  # set by serverless-wsgi plugin

REGION = os.getenv('REGION', 'ap-southeast-2')
DEPLOYMENT_STAGE = os.getenv('DEPLOYMENT_STAGE', 'LOCAL').upper()
STACK_NAME = os.getenv('STACK_NAME', 'nshm_hazard_graphql_api')

S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', "S3_BUCKET_NAME_unconfigured")
LOGGING_CFG = os.getenv('LOGGING_CFG', 'graphql_api/logging_aws.yaml')
ENABLE_METRICS = bool(os.getenv('ENABLE_METRICS', '').upper() in ["1", "Y", "YES", "TRUE"])
CW_METRICS_RESOLUTION = os.getenv('CW_METRICS_RESOLUTION', 60)  # 1 for high resolution or 60
DISAGGS_KEY = os.environ.get('DISAGGS_KEY', "DISAGGS_KEY/is/unconfigured.json")
PUBLICATIONS_KEY = os.environ.get('PUBLICATIONS_KEY', "PUBLICATIONS_KEY/is/unconfigured.json")

TEXT_CONTENT_INDEX_KEY = os.environ.get('TEXT_CONTENT_INDEX_KEY', "TEXT_CONTENT_INDEX_KEY/is/unconfigured.json")
TEXT_CONTENT_FOLDER_KEY = os.environ.get('TEXT_CONTENT_FOLDER_KEY', "TEXT_CONTENT_FOLDER_KEY/is/not/known")
