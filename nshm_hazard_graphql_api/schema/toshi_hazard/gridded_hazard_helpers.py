import io
import logging
import zipfile
from datetime import datetime as dt
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Tuple, Union

# from nzshm_grid_loc.io import load_polygon_file
import geopandas as gpd
import pandas as pd
from shapely import wkt
from shapely.geometry import Polygon

from nshm_hazard_graphql_api.cloudwatch import ServerlessMetricWriter

log = logging.getLogger(__name__)
db_metrics = ServerlessMetricWriter(metric_name="MethodDuration")


class CustomPolygon:
    def __init__(self, polygon: Polygon, location: Tuple[float, float]):
        self._polygon = polygon
        self._location = location

    def polygon(self) -> Polygon:
        return self._polygon

    def location(self) -> Tuple[float, float]:
        return self._location

    def __hash__(self):
        return hash((self._polygon.wkt, self._location))

    def __eq__(self, other):
        return self._polygon == other._polygon and self._location == other._location


def inner_tiles(clipping_parts: Iterable[CustomPolygon], tiles: Iterable[CustomPolygon]) -> Iterable[CustomPolygon]:
    """Filter tiles, yielding only those that are completely covered by a clipping part.

    This can yield a tile more than once if the clipping_parts overlap can to cover that tile.
    """
    for nz_part in clipping_parts:
        for tile in tiles:
            if nz_part.polygon().covers(tile.polygon()):
                yield tile


def edge_tiles(clipping_parts: Iterable[CustomPolygon], tiles: Iterable[CustomPolygon]) -> Iterable[CustomPolygon]:
    """Filter tiles, yielding only those that intersect a clipping_part and clipping them to that intersection."""
    for nz_part in clipping_parts:
        for tile in tiles:
            if nz_part.polygon().intersects(tile.polygon()):
                try:
                    clipped = CustomPolygon(nz_part.polygon().intersection(tile.polygon()), tile.location())
                    if not clipped.polygon().geom_type == 'Point':
                        yield clipped
                    else:
                        raise RuntimeError("Clipped tile %s is not a Polygon" % (repr(clipped.polygon())))
                except (Exception) as err:
                    log.warning("edge_tiles raised error: %s" % err)


def load_zip(file_name: str) -> Tuple[str, io.BytesIO]:
    """
    Extracts a file from a zip file. The file that is extracted must have a file name equal to the name of the zip file
    minus '.zip'
    :param file_name: the file name of the zip file
    :return: the inner file name and an io.BytesIO object with the file data
    """
    with open(file_name, 'rb') as f:
        with zipfile.ZipFile(f) as fz:
            inner_file_name = fz.namelist()[0]
            data = io.BytesIO(fz.read(inner_file_name))
    return inner_file_name, data


def load_wkt_csv(file_name_or_file):
    """
    Loads a CSV with a "geometry" column that has WKT values in a GeoDataFrame
    :param file_name_or_file:
    :return:
    """
    df = pd.read_csv(file_name_or_file)
    df['geometry'] = df['geometry'].apply(wkt.loads)
    gdf = gpd.GeoDataFrame(df, crs='epsg:4326')
    return gdf


def load_polygon_file(file_name: str) -> gpd.GeoDataFrame:
    """
    Loads a polygon file into a GeodataFrame. Can load everything that geopandas can read plus .wkt.csv and .wkt.csv.zip
    :param file_name: path to a geometry file
    :return: a GeoDataFrame
    """
    file: Union[str, io.BytesIO] = file_name
    if file_name.endswith('.zip'):
        file_name, file = load_zip(file_name)

    if file_name.endswith(".wkt.csv"):
        return load_wkt_csv(file)
    else:
        return gpd.read_file(file)


@lru_cache
def nz_simplified_polygons() -> Tuple[CustomPolygon, ...]:

    small_nz = Path(__file__).parent.parent.parent / 'resources' / 'small-nz.wkt.csv.zip'
    nzdf = load_polygon_file(str(small_nz))
    nz_parts = nzdf['geometry'].tolist()
    # try to remove holes
    nz_parts_whole = []
    for part in nz_parts:
        nz_parts_whole.append(
            CustomPolygon(Polygon(part.exterior.coords), (float(part.centroid.x), float(part.centroid.y)))
        )
    return tuple(nz_parts_whole)


@lru_cache
def clip_tiles(clipping_parts: Tuple[CustomPolygon], tiles: Tuple[CustomPolygon]):
    t0 = dt.utcnow()
    covered_tiles = set(inner_tiles(clipping_parts, tiles))
    db_metrics.put_duration(__name__, 'filter_inner_tiles', dt.utcnow() - t0)

    outer_tiles = set(tiles).difference(covered_tiles)

    t0 = dt.utcnow()
    clipped_tiles = set(edge_tiles(clipping_parts, outer_tiles))
    db_metrics.put_duration(__name__, 'clip_outer_tiles', dt.utcnow() - t0)

    log.info('filtered %s tiles to %s inner in %s' % (len(tiles), len(covered_tiles), dt.utcnow() - t0))
    log.info('clipped %s edge tiles to %s in %s' % (len(outer_tiles), len(clipped_tiles), dt.utcnow() - t0))

    new_geometry = covered_tiles.union(clipped_tiles)
    return tuple(new_geometry)
