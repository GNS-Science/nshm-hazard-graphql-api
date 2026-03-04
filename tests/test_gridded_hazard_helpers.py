"""Tests for gridded hazard helper functions."""

import pytest

from nshm_hazard_graphql_api.schema.toshi_hazard.gridded_hazard_helpers import (
    clip_tiles,
    nz_simplified_polygons,
)
from nshm_hazard_graphql_api.schema.toshi_hazard.gridded_hazard import get_tile_polygons
from nzshm_common.grids import RegionGrid

GRID = "NZ_0_1_NB_1_1"


@pytest.fixture()
def tile_polygons():
    yield get_tile_polygons(GRID)


@pytest.mark.skip("failing now because clip_tiles is duplicating tiles")
def test_nz_clipping_returns_unique_locations(tile_polygons):

    assert len(tile_polygons) == 3741

    nz_parts = nz_simplified_polygons()
    locs = sorted([f.location() for f in nz_parts])
    assert len(locs) == len(set(locs))
    print(len(nz_parts))

    assert len(nz_parts) == 39

    new_geometry = clip_tiles(nz_parts, tile_polygons)

    locs = sorted([f.location() for f in new_geometry])
    print(locs[0])
    assert len(locs) == len(set(locs))


@pytest.mark.skip("REFACTOR")
def test_get_gridded_hazard_uniqueness():

    grid = RegionGrid[GRID].load()

    assert len(grid) == 3741
    nz_parts = nz_simplified_polygons()
    print(nz_parts)

    polygons = get_tile_polygons(GRID)
    assert len(polygons) == 3741

    nz_parts = nz_simplified_polygons()
    new_geometry = clip_tiles(nz_parts, polygons)

    locs = [f.location() for f in new_geometry]

    print(locs[0])
    assert len(locs) == len(set(locs))
    assert len(locs) == 3402

    assert len(new_geometry) == 3402
    print(new_geometry[0])
