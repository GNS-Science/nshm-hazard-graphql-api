"""Build Gridded Hazard."""

import json
import logging
import math
import os
from datetime import datetime as dt
from functools import lru_cache
from typing import Iterable, Tuple, Union

import geopandas as gpd
import graphene
import matplotlib as mpl
from nzshm_common.geometry.geometry import create_square_tile
from nzshm_common.grids import RegionGrid
from toshi_hazard_store import query

from nshm_hazard_graphql_api.cloudwatch import ServerlessMetricWriter

from .gridded_hazard_helpers import CustomPolygon, clip_tiles, nz_simplified_polygons
from .hazard_schema import GriddedLocation

log = logging.getLogger(__name__)

RegionGridEnum = graphene.Enum.from_enum(RegionGrid)

db_metrics = ServerlessMetricWriter(metric_name="MethodDuration")


class ColourScaleNormalise(graphene.Enum):
    LOG = "log"
    LIN = "lin"


COLOR_SCALE_NORMALISE_LOG = 'log' if os.getenv('COLOR_SCALE_NORMALISATION', '').upper() == 'LOG' else 'lin'


class HexRgbValueMapping(graphene.ObjectType):
    levels = graphene.List(graphene.Float)
    hexrgbs = graphene.List(graphene.String)


@lru_cache
def get_normaliser(color_scale_vmax, color_scale_vmin, color_scale_normalise):
    if color_scale_normalise == ColourScaleNormalise.LOG:
        log.debug("resolve_hazard_map using LOG normalized colour scale")
        norm = mpl.colors.LogNorm(vmin=color_scale_vmin, vmax=color_scale_vmax)
    else:
        color_scale_vmin = color_scale_vmin or 0
        log.debug("resolve_hazard_map using LIN normalized colour scale")
        norm = mpl.colors.Normalize(vmin=color_scale_vmin, vmax=color_scale_vmax)
    return norm


@lru_cache
def get_colour_scale(color_scale: str, color_scale_normalise, vmax: float, vmin: float) -> HexRgbValueMapping:
    # build the colour_scale
    assert vmax * 2 == int(vmax * 2)  # make sure we have a value on a 0.5 interval
    levels, hexrgbs = [], []
    cmap = mpl.colormaps[color_scale]
    norm = get_normaliser(vmax, vmin, color_scale_normalise)
    for level in range(0, int(vmax * 10) + 1):
        levels.append(level / 10)
        hexrgbs.append(mpl.colors.to_hex(cmap(norm(level / 10))))
    hexrgb = HexRgbValueMapping(levels=levels, hexrgbs=hexrgbs)
    return hexrgb


@lru_cache
def get_colour_values(
    color_scale: str,
    color_scale_vmax: float,
    color_scale_vmin: float,
    color_scale_normalise: str,
    values: Tuple[Union[float, None]],
) -> Iterable[str]:
    # grid colours
    log.debug('color_scale_vmax: %s' % color_scale_vmax)
    norm = get_normaliser(color_scale_vmax, color_scale_vmin, color_scale_normalise)
    cmap = mpl.colormaps[color_scale]
    colors = []
    # Some grids have missing values, we'll set these to black
    for i, v in enumerate(values):
        if v is None:
            colors.append("x000000")
        else:
            colors.append(mpl.colors.to_hex(cmap(norm(v)), keep_alpha=True))
    return colors


@lru_cache
def get_tile_polygons(grid_id: str) -> Tuple[CustomPolygon, ...]:
    # build the hazard_map
    t0 = dt.utcnow()
    region_grid = RegionGrid[grid_id]
    grid = region_grid.load()
    geometry = []
    for idx, pt in enumerate(grid):
        tile = CustomPolygon(create_square_tile(region_grid.resolution, pt[1], pt[0]), location=(pt[1], pt[0]))
        geometry.append(tile)
    log.debug('built %s tiles in %s' % (len(geometry), dt.utcnow() - t0))
    return tuple(geometry)


@lru_cache
def polygon_centers(polygons):
    return tuple([tuple([p.location()[0], p.location()[1]]) for p in polygons])


@lru_cache
def values_for_clipped_tiles(clipped_tiles, polygons, poes):
    res = []

    def location_poes(polygons, poes):
        return dict(zip(polygon_centers(polygons), poes))

    location_poe_mapping = location_poes(polygons, poes)
    for tile in clipped_tiles:
        res.append(location_poe_mapping[tuple([tile.location()[0], tile.location()[1]])])
    return tuple(res)


@lru_cache
def cacheable_hazard_map(
    hazard_model: str,
    grid_id: str,
    vs30: int,
    poe: float,
    agg: str,
    imt: str,
    values: Tuple[float],
    color_scale: str,
    color_scale_vmax: float,
    color_scale_vmin: float,
    color_scale_normalise: str,
    fill_opacity: float,
    stroke_opacity: float,
    stroke_width: float,
):
    t0 = dt.utcnow()
    log.info(
        'cacheable_hazard_map() vs30: %s, imt: %s, poe: %s, agg: %s, hazard_model: %s, grid_id: %s'
        % (vs30, imt, poe, agg, hazard_model, grid_id)
    )

    nz_parts = nz_simplified_polygons()  # cached
    log.debug('nz_simplified_polygons cache_info: %s' % str(nz_simplified_polygons.cache_info()))

    polygons = get_tile_polygons(grid_id)
    log.debug('get_tile_polygon cache_info: %s' % str(get_tile_polygons.cache_info()))

    new_geometry = clip_tiles(nz_parts, polygons)
    log.debug('clip_tiles cache_info: %s' % str(clip_tiles.cache_info()))

    log.debug(
        'len(values) %s; len(polygons) %s; len(new_geometry) %s' % (len(values), len(polygons), len(new_geometry))
    )

    t1 = dt.utcnow()
    log.debug('time to build geometry of %s polygons took %s' % (len(new_geometry), (t1 - t0)))

    values = values_for_clipped_tiles(new_geometry, polygons, values)
    assert len(new_geometry) == len(values)
    t2 = dt.utcnow()
    log.debug('values_for_clipped_tiles cache_info: %s' % str(values_for_clipped_tiles.cache_info()))
    log.debug('time to build %s values %s' % (len(values), (t2 - t1)))

    color_scale_vmax = (
        color_scale_vmax
        if color_scale_vmax
        else math.ceil(max((v for v in values if v is not None), default=1) * 2) / 2
    )
    color_scale_vmin = color_scale_vmin or min((v for v in values if v is not None), default=0)

    log.debug('color_scale_normalise %s' % color_scale_normalise)
    color_values = get_colour_values(color_scale, color_scale_vmax, color_scale_vmin, color_scale_normalise, values)

    t3 = dt.utcnow()
    log.debug('cacheable_hazard_map colour map took  %s' % (t3 - t2))
    log.debug('get_colour_values cache_info: %s' % str(get_colour_values.cache_info()))

    colour_scale = get_colour_scale(color_scale, color_scale_normalise, vmax=color_scale_vmax, vmin=color_scale_vmin)
    t4 = dt.utcnow()
    log.debug('get_colour_scale took  %s' % (t4 - t3))
    log.debug('get_colour_scale cache_info: %s' % str(get_colour_scale.cache_info()))

    gdf = gpd.GeoDataFrame(
        data=dict(
            loc=[g.location() for g in new_geometry],
            geometry=[g.polygon() for g in new_geometry],
            value=values,
            fill=color_values,
            fill_opacity=[fill_opacity for n in values],
            stroke=color_values,
            stroke_width=[stroke_width for n in values],
            stroke_opacity=[stroke_opacity for n in values],
        )
    )
    gdf = gdf.rename(
        columns={'fill_opacity': 'fill-opacity', 'stroke_width': 'stroke-width', 'stroke_opacity': 'stroke-opacity'}
    )

    # filter out polygons with missing values
    gdf = gdf[~gdf["value"].isnull()]

    t5 = dt.utcnow()
    log.debug('build geojson took  %s' % (t5 - t4))

    t1 = dt.utcnow()
    log.debug('cacheable_hazard_map took %s' % (t1 - t0))
    db_metrics.put_duration(__name__, 'cacheable_hazard_map', t1 - t0)
    return GeoJsonHazardMap(geojson=json.loads(gdf.to_json()), colour_scale=colour_scale)


class GeoJsonHazardMap(graphene.ObjectType):
    geojson = graphene.JSONString()
    colour_scale = graphene.Field(HexRgbValueMapping)


class GriddedHazard(graphene.ObjectType):
    grid_id = graphene.Field(RegionGridEnum)
    hazard_model = graphene.String()
    imt = graphene.String()
    agg = graphene.String()
    vs30 = graphene.Float()
    poe = graphene.Float()
    values = graphene.List(graphene.Float, description="Acceleration values.")

    hazard_map = graphene.Field(
        GeoJsonHazardMap,
        # Extra args
        color_scale=graphene.String(default_value='jet', required=False),
        color_scale_vmax=graphene.Float(required=False),
        color_scale_vmin=graphene.Float(default_value=0.0, required=False),
        color_scale_normalise=graphene.Argument(ColourScaleNormalise, required=False),
        stroke_width=graphene.Float(default_value='0.1', required=False),
        stroke_opacity=graphene.Float(default_value='1.0', required=False),
        fill_opacity=graphene.Float(default_value='1.0', required=False),
    )

    grid_locations = graphene.List(GriddedLocation)

    def resolve_hazard_map(root, info, **args):
        """Resolve gridded hazard to geojson with formatting options."""
        t0 = dt.utcnow()
        hazmap = cacheable_hazard_map(
            root.hazard_model,
            root.grid_id.name,
            root.vs30,
            root.poe,
            root.agg,
            root.imt,
            tuple(root.values),
            color_scale=args['color_scale'],
            color_scale_vmax=args.get('color_scale_vmax'),
            color_scale_vmin=args.get('color_scale_vmin'),
            color_scale_normalise=args.get('color_scale_normalise', COLOR_SCALE_NORMALISE_LOG),
            fill_opacity=args['fill_opacity'],
            stroke_opacity=args['stroke_opacity'],
            stroke_width=args['stroke_width'],
        )
        t1 = dt.utcnow()
        log.debug('cacheable_hazard_map cache_info: %s' % str(cacheable_hazard_map.cache_info()))
        db_metrics.put_duration(__name__, 'resolve_hazard_map', t1 - t0)
        return hazmap


class GriddedHazardResult(graphene.ObjectType):
    gridded_hazard = graphene.Field(graphene.List(GriddedHazard))
    ok = graphene.Boolean()


@lru_cache
def cacheable_gridded_hazard_query(
    hazard_model_id: str, location_grid_id: str, vs30: int, imt: str, agg: str, poe: float
):

    log.debug(
        'cacheable_gridded_hazard_query with %s %s %s %s %s %s'
        % (hazard_model_id, location_grid_id, vs30, imt, agg, poe)
    )

    return list(
        query.get_one_gridded_hazard(
            hazard_model_id,
            location_grid_id,
            vs30,
            imt,
            agg,
            poe,
        )
    )


def query_gridded_hazard(kwargs):
    """Run query against dynamoDB."""
    t0 = dt.utcnow()
    log.info('query_gridded_hazard args: %s' % kwargs)

    def build_hazard_from_query_response(result):
        log.info("build_hazard_from_query_response %s" % result)
        for obj in result:
            yield GriddedHazard(
                grid_id=RegionGridEnum[obj.location_grid_id],
                hazard_model=obj.hazard_model_id,
                vs30=obj.vs30,
                imt=obj.imt,
                agg=obj.agg,
                poe=obj.poe,
                values=obj.grid_poes,
            )

    response = cacheable_gridded_hazard_query(
        hazard_model_id=kwargs['hazard_model_id'],
        location_grid_id=RegionGridEnum.get(kwargs['grid_id']).name,
        vs30=kwargs['vs30'],
        imt=kwargs['imt'],
        agg=kwargs['agg'],
        poe=kwargs['poe'],
    )

    res = GriddedHazardResult(ok=True, gridded_hazard=build_hazard_from_query_response(response))
    db_metrics.put_duration(__name__, 'query_gridded_hazard', dt.utcnow() - t0)
    return res
