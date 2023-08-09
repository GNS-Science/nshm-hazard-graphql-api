"""Build Hazard curves from the old dynamoDB models."""
import io
import json
import logging
from datetime import datetime as dt
from typing import Iterator

import boto3
from nzshm_common.location import CodedLocation, location

from nshm_hazard_graphql_api.cloudwatch import ServerlessMetricWriter
from nshm_hazard_graphql_api.config import DISAGGS_KEY, S3_BUCKET_NAME

from .hazard_schema import DisaggregationReport, DisaggregationReportResult, HazardCodedLocation

log = logging.getLogger(__name__)

db_metrics = ServerlessMetricWriter(metric_name="MethodDuration")


def fetch_data() -> Iterator:
    log.debug("fetch_data() %s from %s " % (DISAGGS_KEY, S3_BUCKET_NAME))
    s3 = boto3.resource('s3')
    s3obj = s3.Object(S3_BUCKET_NAME, DISAGGS_KEY)
    file_object = io.BytesIO()
    s3obj.download_fileobj(file_object)
    file_object.seek(0)
    return json.load(file_object)


def disaggregation_reports(kwargs):
    """Run query against"""
    t0 = dt.utcnow()

    def build_disaggs() -> Iterator[DisaggregationReport]:
        log.info("build_disaggs")
        for obj in fetch_data():
            loc = location.LOCATIONS_BY_ID[obj['location_key']]
            coded_loc = CodedLocation(loc['latitude'], loc['longitude'], 0.01)
            hazard_loc = HazardCodedLocation(
                lat=coded_loc.lat, lon=coded_loc.lon, key=loc['id'], name=loc['name'], code=coded_loc.code
            )
            yield DisaggregationReport(
                hazard_model=obj['hazard_model'],
                vs30=obj['vs30'],
                imt=obj['imt'],
                location=hazard_loc,
                poe=obj['poe'],
                inv_time=obj['inv_time'],
                report_url=obj['report_url'],
            )

    res = DisaggregationReportResult(ok=True, reports=build_disaggs())
    db_metrics.put_duration(__name__, 'disaggregations', dt.utcnow() - t0)
    return res
