"""query interfaces for pyarrow datasets"""

import datetime as dt
import logging

from toshi_hazard_store.query import datasets as ths_datasets

from nshm_hazard_graphql_api.cloudwatch import ServerlessMetricWriter

db_metrics = ServerlessMetricWriter(metric_name="MethodDuration")

log = logging.getLogger(__name__)


def get_hazard_curves(location_codes, vs30s, hazard_model, imts, aggs, strategy: str):
    """
    Retrieves aggregated hazard curves from the dataset.

    Args:
      location_codes (list): List of location codes.
      vs30s (list): List of VS30 values.
      hazard_model (list): List of hazard model IDs.
      imts (list): List of intensity measure types (e.g. 'PGA', 'SA(5.0)').
      aggs (list): List of aggregation types.
      strategy: which query strategy to use -  lambda likes `d2`.

    Yields:
      AggregatedHazard: An object containing the aggregated hazard curve data.
    """
    log.debug('> get_hazard_curves()')
    t0 = dt.datetime.now()

    count = 0

    if strategy == "d2":
        qfn = ths_datasets.get_hazard_curves_by_vs30_nloc0
    elif strategy == "d1":
        qfn = ths_datasets.get_hazard_curves_by_vs30
    else:
        qfn = ths_datasets.get_hazard_curves_naive

    deferred_warning = None
    try:
        for obj in qfn(location_codes, vs30s, hazard_model, imts, aggs):
            count += 1
            yield obj
    except RuntimeWarning as err:
        if "Failed to open dataset" in str(err):
            deferred_warning = err
        else:
            raise err  # pragma: no cover

    t1 = dt.datetime.now()
    log.info(f"Executed dataset query for {count} curves in {(t1 -t0).total_seconds()} seconds.")
    delta = t1 - t0
    db_metrics.put_duration(__name__, 'hazard_curves', delta)

    if deferred_warning:
        raise deferred_warning
