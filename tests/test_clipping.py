"""Tests for toshi_hazard_rev module."""

import unittest
from datetime import datetime as dt
from nzshm_common.grids import RegionGrid
from nzshm_common.geometry.geometry import create_square_tile

from shapely.geometry import Polygon

from nshm_hazard_graphql_api.schema.toshi_hazard.gridded_hazard_helpers import (
    CustomPolygon,
    clip_tiles,
    nz_simplified_polygons,
)

GRID = 'WLG_0_01_nb_1_1'


class TestCustomPolygon(unittest.TestCase):
    def test_custom_class_is_hashable(self):

        pA = CustomPolygon(Polygon([(0, 0), (1, 1), (1, 0)]), (0, 1))
        pB = CustomPolygon(Polygon([(0, 0), (1, 1), (1, 0)]), (0, 2))

        setA = set([pA])
        setB = set([pA, pB])

        self.assertEqual(setA.intersection(setB), set([pA]))


class TestGriddedHazard(unittest.TestCase):
    def test_get_clipped_grid(self):

        region_grid = RegionGrid[GRID]
        grid = region_grid.load()
        geometry = []

        t0 = dt.utcnow()

        # build the hazard_map
        for pt in grid:
            tile = CustomPolygon(
                create_square_tile(region_grid.resolution, pt[1], pt[0]),
                location=(pt[1], pt[0]),
            )
            geometry.append(tile)
        print('built %s tiles in %s' % (len(geometry), dt.utcnow() - t0))

        nz_parts = nz_simplified_polygons()

        new_geometry = clip_tiles(nz_parts, tuple(geometry))
        self.assertEqual(len(new_geometry), 763)

        # gdf = gpd.GeoDataFrame(data=dict(geometry=[g.polygon() for g in new_geometry],
        # value=[g.value() for g in new_geometry]))

        # with open('dump_new_clipped.json', 'w') as f:
        #     f.write(gdf.to_json())

        # with open('nz_small.json', 'w') as f:
        #     f.write(nzdf.to_json())

        # for pt in grid:
        #     geometry.append(create_square_tile(region_grid.resolution, pt[1], pt[0]))
        # print('built %s wlg tiles in %s' % (len(geometry), dt.utcnow() - t0))
        # print(nzdf)
        # assert 0
