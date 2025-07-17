"""Build Hazard curves from either dynamoDB models or from new dataset."""

import logging
from functools import lru_cache
from typing import Iterable, Iterator, Optional

from nzshm_common.location import CodedLocation, location
from toshi_hazard_store import query_v3

from nshm_hazard_graphql_api.cloudwatch import ServerlessMetricWriter
from nshm_hazard_graphql_api.config import DATASET_AGGR_ENABLED

from . import datasets
from .hazard_schema import GriddedLocation, ToshiHazardCurve, ToshiHazardCurveResult, ToshiHazardResult

log = logging.getLogger(__name__)
db_metrics = ServerlessMetricWriter(metric_name="MethodDuration")

DATASET_VS30 = [200, 400, 1500]  # temporary measure while only some vs3 are in dataset


@lru_cache
def match_named_location_coord_code(location_code: str) -> Optional[GriddedLocation]:
    """Attempt to match a Named Location.

    If the provided coordinates match named_location, returns a complete GriddedLocation

    Returns:
        GriddedLocation: or None
    """

    resolution: float = 0.001
    log.debug("match_named_location_coord_code %s res: %s" % (location_code, resolution))

    tloc = CodedLocation(*[float(x) for x in location_code.split('~')], resolution)

    for loc in location.LOCATIONS_BY_ID:
        site = location.LOCATIONS_BY_ID[loc]

        named_location = CodedLocation(site['latitude'], site['longitude'], resolution)

        if tloc == named_location:
            # tloc = tloc.resample(0.001)
            # TODO: this object should be NamedLocation not GriddedLocation
            return GriddedLocation(
                lat=tloc.lat,
                lon=tloc.lon,
                code=tloc.code,
                resolution=tloc.resolution,
                name=site.get('name'),
                key=site.get('id'),
            )
    return None


def normalise_locations(locations: Iterable[str], resolution: float = 0.01) -> Iterator[GriddedLocation]:
    """Normalises a list of location codes or names into GriddedLocations.

    Args:
        locations (Iterable[str]): A list of location codes or names.
        resolution (float, optional): The resolution to use for the normalised
            location. Defaults to 0.01.

    Yields:
        Iterator[GriddedLocation]: Normalised locations as GriddedLocations.
    """
    for loc in locations:
        # Check if this is a location name ID eg "WLG" and if so, convert to the legit code
        if loc in location.LOCATIONS_BY_ID:
            site = location.LOCATIONS_BY_ID[loc]
            cloc = CodedLocation(site['latitude'], site['longitude'], 0.001)  # NamedLocation have 0.001 resolution
            yield GriddedLocation(
                lat=cloc.lat,
                lon=cloc.lon,
                code=cloc.code,
                resolution=cloc.resolution,
                name=site.get('name'),
                key=site.get('id'),
            )
            continue

        # TODO this behaviour will be deprecated
        # do these coordinates match a named location?, if so convert to the legit code.
        matched = match_named_location_coord_code(loc)
        if matched:
            log.debug('normalise_locations got named location: %s code: %s' % (matched.name, matched.code))
            yield matched
            continue

        # TODO: if we don't match a named location, this falls back to default grid resolution
        cloc = CodedLocation(*[float(x) for x in loc.split('~')], resolution)
        yield GriddedLocation(lat=cloc.lat, lon=cloc.lon, code=cloc.code, resolution=cloc.resolution)


def hazard_curves(kwargs: dict) -> ToshiHazardCurveResult:
    """
    Run query against data source.

    Source can be either DynamoDB usign v3 query, or the new Dataset.

    Args:
        kwargs (dict): Query arguments.

    Returns:
        ToshiHazardCurveResult: Result of the query.
    """

    def get_curve(obj):
        levels, values = [], []
        for lv in obj.values:
            levels.append(float(lv.lvl))
            values.append(float(lv.val))
        return ToshiHazardCurve(levels=levels, values=values)

    def build_response_from_query(result: list, resolution: float) -> Iterator[ToshiHazardResult]:
        log.info("build_response_from_query")
        try:
            for obj in result:
                named = match_named_location_coord_code(obj.nloc_001)
                if named:
                    log.debug('build_response_from_query got named location: %s' % named)
                    loc_code = named.code
                else:
                    # log.debug('resolve with : %s degrees of precision' % resolution)
                    loc_code = CodedLocation(*[float(x) for x in obj.nloc_001.split('~')], resolution).code
                    # loc_code = obj.nloc_001

                yield ToshiHazardResult(
                    hazard_model=obj.hazard_model_id,
                    vs30=obj.vs30,
                    imt=obj.imt,
                    loc=loc_code,
                    agg=obj.agg,
                    curve=get_curve(obj),
                )
        except RuntimeWarning as exc:
            log.warning(exc)

    query_strategy = kwargs.get("query_strategy", "d2")

    gridded_locations = list(normalise_locations(kwargs['locs'], kwargs['resolution']))
    coded_locations = [
        CodedLocation(lat=loc.lat, lon=loc.lon, resolution=loc.resolution).resample(0.001).code
        for loc in gridded_locations
    ]

    log.info(
        f"pre query DATASET_AGGR_ENABLED: {DATASET_AGGR_ENABLED} {set(DATASET_VS30).issuperset(set(kwargs['vs30s']))}"
        f" {set(DATASET_VS30)} {set(kwargs['vs30s'])}"
        f" strategy: {query_strategy}"
    )
    if (
        query_strategy in ["d0", "d1", "d2"]
        and DATASET_AGGR_ENABLED
        and set(DATASET_VS30).issuperset(set(kwargs['vs30s']))
    ):
        log.info('DATASET QUERY')
        query_res = datasets.get_hazard_curves(
            coded_locations,
            kwargs['vs30s'],
            kwargs['hazard_model'],
            kwargs['imts'],
            aggs=kwargs['aggs'],
            strategy=query_strategy,
        )
    else:
        # old dynamodB query
        log.info('DYNAMODB QUERY')
        query_res = query_v3.get_hazard_curves(
            coded_locations, kwargs['vs30s'], [kwargs['hazard_model']], kwargs['imts'], aggs=kwargs['aggs']
        )

    result = ToshiHazardCurveResult(
        ok=True, locations=gridded_locations, curves=build_response_from_query(query_res, kwargs['resolution'])
    )
    return result
