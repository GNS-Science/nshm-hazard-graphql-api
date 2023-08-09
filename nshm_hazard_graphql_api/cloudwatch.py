#!cloudwatch

import datetime
import logging
import os

import boto3

from nshm_hazard_graphql_api.config import ENABLE_METRICS, REGION, STACK_NAME

log = logging.getLogger(__name__)


class ServerlessMetricWriter:
    def __init__(self, metric_name, resolution=60):
        self._lambda_name = STACK_NAME
        self._metric_name = metric_name
        self._resolution = resolution  # 1=high, or 60
        self._client = boto3.client('cloudwatch', region_name=REGION)

    def put_duration(self, package, operation, duration):

        if isinstance(duration, datetime.timedelta):
            duration = float(duration.seconds / 1e6 + (duration.microseconds / 1e3))

        rec = dict(
            Namespace=f'AWS/Lambda/{self._lambda_name}',
            MetricData=[
                {
                    'MetricName': self._metric_name,
                    'Dimensions': [{'Name': 'Package', 'Value': package}, {'Name': 'Operation', 'Value': operation}],
                    'Timestamp': datetime.datetime.now(),
                    'Value': duration,
                    'Unit': 'Milliseconds',
                    'StorageResolution': self._resolution,
                }
            ],
        )
        log.debug(
            'ENABLE_METRICS for %s = %s (os: %s)'
            % (self._metric_name, ENABLE_METRICS, bool(os.getenv('ENABLE_METRICS')))
        )
        if ENABLE_METRICS:
            self._client.put_metric_data(**rec)
