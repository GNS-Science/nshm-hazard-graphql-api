"""query interfaces for pyarrow datasets"""

import datetime as dt
import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Union

import pyarrow.compute as pc
import pyarrow.dataset as ds
from toshi_hazard_store.model.pyarrow.dataset_schema import get_hazard_aggregate_schema

from nshm_hazard_graphql_api.config import DATASET_AGGR_URI

log = logging.getLogger(__name__)

IMT_44_LVLS = [
    0.0001,
    0.0002,
    0.0004,
    0.0006,
    0.0008,
    0.001,
    0.002,
    0.004,
    0.006,
    0.008,
    0.01,
    0.02,
    0.04,
    0.06,
    0.08,
    0.1,
    0.2,
    0.3,
    0.4,
    0.5,
    0.6,
    0.7,
    0.8,
    0.9,
    1.0,
    1.2,
    1.4,
    1.6,
    1.8,
    2.0,
    2.2,
    2.4,
    2.6,
    2.8,
    3.0,
    3.5,
    4.0,
    4.5,
    5.0,
    6.0,
    7.0,
    8.0,
    9.0,
    10.0,
]


@dataclass
class IMTValue:
    lvl: float
    val: float


@dataclass
class AggregatedHazard:
    """
    For Table schema:
            ("compatible_calc_id", pyarrow.string()),  # for hazard-calc equivalence, for PSHA engines interoperability
            ("hazard_model_id", pyarrow.string()),  # the model that these curves represent.
            ("nloc_001", pyarrow.string()),  # the location string to three places e.g. "-38.330~17.550"
            ("nloc_0", pyarrow.string()),  # the location string to zero places e.g.  "-38.0~17.0" (used for partioning)
            ('imt', pyarrow.string()),  # the imt label e.g. 'PGA', 'SA(5.0)'
            ('vs30', vs30_type),  # the VS30 integer
            ('aggr', pyarrow.string()),  # the the aggregation type
            ("values", values_type),  # a list of the 44 IMTL values
    """

    compatable_calc_id: str
    hazard_model_id: str
    nloc_001: str
    nloc_0: str
    imt: str
    vs30: int
    agg: str
    values: list[Union[float, IMTValue]]

    def to_imt_values(self):
        new_values = zip(IMT_44_LVLS, self.values)
        self.values = [IMTValue(*x) for x in new_values]
        return self


@lru_cache
def get_dataset():
    """Cache the dataset"""
    t0 = dt.datetime.now()
    dataset = ds.dataset(DATASET_AGGR_URI, partitioning='hive', format='parquet', schema=get_hazard_aggregate_schema())
    t1 = dt.datetime.now()
    log.info(f"Opened dataset `{DATASET_AGGR_URI}` in {(t1 -t0).total_seconds()} seconds.")
    return dataset


def get_hazard_curves(location_codes, vs30s, hazard_model, imts, aggs):
    t0 = dt.datetime.now()
    dataset = get_dataset()

    # location_codes = [f'"{x.code}"' for x in coded_locations]
    filter = (
        (pc.field('aggr').isin(aggs))
        & (pc.field("nloc_001").isin(location_codes))
        & (pc.field("imt").isin(imts))
        & (pc.field("vs30").isin(vs30s))
        & (pc.field('hazard_model_id').isin(hazard_model))
    )

    print(filter)

    table = dataset.to_table(filter=filter)
    print(table.schema)
    count = 0
    for batch in table.to_batches():
        # print(batch.columns)
        for row in zip(*batch.columns):
            count += 1

            deets = (x.as_py() for x in row)
            obj = AggregatedHazard(*deets).to_imt_values()
            print(obj)
            # assert 0, "BOMB"
            assert obj.vs30 in vs30s, f"vs30 {obj.vs30} not in {vs30s}"
            yield obj

    t1 = dt.datetime.now()
    log.info(f"Executed dataset query for {count} curves in {(t1 -t0).total_seconds()} seconds.")
