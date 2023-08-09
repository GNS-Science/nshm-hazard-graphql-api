"""The main API schema."""

import logging

import graphene
from graphene import relay
from nzshm_common.location import CodedLocation

import nshm_hazard_graphql_api

from .toshi_hazard import (
    GriddedHazardResult,
    GriddedLocation,
    GriddedLocationResult,
    RegionGridEnum,
    ToshiHazardCurveResult,
    hazard_curves,
    query_gridded_hazard,
)

log = logging.getLogger(__name__)


class QueryRoot(graphene.ObjectType):
    """This is the entry point for all graphql query operations"""

    node = relay.Node.Field()

    about = graphene.String(description='About this API ')

    gridded_location = graphene.Field(
        GriddedLocationResult,
        lat=graphene.Argument(graphene.Float),
        lon=graphene.Argument(graphene.Float),
        resolution=graphene.Argument(graphene.Float),
    )

    hazard_curves = graphene.Field(
        ToshiHazardCurveResult,
        hazard_model=graphene.Argument(graphene.String),
        imts=graphene.Argument(graphene.List(graphene.String)),
        locs=graphene.Argument(graphene.List(graphene.String)),
        aggs=graphene.Argument(graphene.List(graphene.String)),
        vs30s=graphene.Argument(graphene.List(graphene.Int)),
        resolution=graphene.Argument(graphene.Float, required=False, default_value=0.1),
    )

    gridded_hazard = graphene.Field(
        GriddedHazardResult,
        grid_id=graphene.Argument(RegionGridEnum),
        hazard_model_id=graphene.Argument(graphene.String),
        imt=graphene.Argument(graphene.String),
        loc=graphene.Argument(graphene.String),
        agg=graphene.Argument(graphene.String),
        vs30=graphene.Argument(graphene.Int),
        poe=graphene.Argument(graphene.Float),
    )

    def resolve_gridded_location(root, info, **kwargs):
        log.info("resolve_gridded_location kwargs %s" % kwargs)
        grid_loc = CodedLocation(kwargs['lat'], kwargs['lon'], kwargs['resolution'])
        return GriddedLocationResult(
            location=GriddedLocation(
                lat=grid_loc.lat, lon=grid_loc.lon, code=grid_loc.code, resolution=grid_loc.resolution
            ),
            ok=True,
        )

    def resolve_gridded_hazard(root, info, **kwargs):
        log.info("resolve_gridded_hazard kwargs %s" % kwargs)
        return query_gridded_hazard(kwargs)

    def resolve_hazard_curves(root, info, **kwargs):
        log.info("resolve_hazard_curves kwargs %s" % kwargs)
        return hazard_curves(kwargs)

    def resolve_about(root, info, **args):
        return f"Hello World, I am nshm_hazard_graphql_api version: {nshm_hazard_graphql_api.__version__}"


schema_root = graphene.Schema(query=QueryRoot, mutation=None, auto_camelcase=False)
