"""Tests for toshi_hazard_rev module."""

import itertools
import random

from nshm_hazard_graphql_api.schema.toshi_hazard.gridded_hazard_helpers import (
    clip_tiles,
    nz_simplified_polygons,
)
from nshm_hazard_graphql_api.schema.toshi_hazard.gridded_hazard import get_tile_polygons

from toshi_hazard_store import model
from nzshm_common.grids import RegionGrid

import pytest

HAZARD_MODEL_ID = 'GRIDDED_THE_THIRD'
vs30s = [250, 400]
imts = ['PGA', 'SA(0.5)']
aggs = ['mean', '0.10']


def build_hazard_aggregation_models(grid_id, hazard_model_id):

    grid = RegionGrid[grid_id].load()
    grid_poes = [random.randint(0, int(4.7e6)) / int(1e6) for x in range(len(grid))]
    grid_poes[0] = 0.1

    for imt, vs30, agg in itertools.product(imts, vs30s, aggs):

        obj = model.GriddedHazard.new_model(
            hazard_model_id=hazard_model_id,
            location_grid_id=grid_id,
            vs30=vs30,
            imt=imt,
            agg=agg,
            poe=0.02,
            grid_poes=grid_poes,
        )
        # print('OBJ', obj)
        yield obj


GRID = 'NZ_0_1_NB_1_1'


@pytest.fixture()
def tile_polygons():
    yield get_tile_polygons(GRID)


@pytest.mark.skip('failing now because clip_tiles is duplicating tiles')
def test_nz_clipping_returns_unique_locations(tile_polygons):

    assert len(tile_polygons) == 3741

    nz_parts = nz_simplified_polygons()
    locs = sorted([f.location() for f in nz_parts])
    assert len(locs) == len(set(locs))
    print(len(nz_parts))

    assert len(nz_parts) == 39

    new_geometry = clip_tiles(nz_parts, tile_polygons)

    # should be 3402 unique locations
    locs = sorted([f.location() for f in new_geometry])
    print(locs[0])
    assert len(locs) == len(set(locs))
    # assert len(locs) == 3402

    # assert len(new_geometry) == 3402
    # print(new_geometry[0])

    # assert 0


@pytest.mark.skip('REFACTOR')
def test_get_gridded_hazard_uniqueness():

    grid = RegionGrid[GRID].load()

    assert len(grid) == 3741
    nz_parts = nz_simplified_polygons()
    print(nz_parts)

    values = tuple(build_hazard_aggregation_models(GRID, HAZARD_MODEL_ID))
    assert len(values) == 8  # 1 for each imt, vs30, agg permutation

    polygons = get_tile_polygons(GRID)
    assert len(polygons) == 3741
    # should be 3402 unique locations

    nz_parts = nz_simplified_polygons()
    new_geometry = clip_tiles(nz_parts, polygons)

    locs = [f.location() for f in new_geometry]

    print(locs[0])
    assert len(locs) == len(set(locs))
    assert len(locs) == 3402

    assert len(new_geometry) == 3402
    print(new_geometry[0])

    assert 0

    # self.assertEqual(len(features), len(new_geometry))

    # locs = [tuple(f["properties"]["loc"]) for f in features]
    # assert len(locs) == len(set(locs))
    # print(features[0])
    # self.assertEqual(len(features), len(grid))  # one tile dropped

    # self.assertTrue(max(res['gridded_hazard'][0]['values']) < 4.7)
    # self.assertTrue(max(res['gridded_hazard'][0]['values']) > 4.5)
