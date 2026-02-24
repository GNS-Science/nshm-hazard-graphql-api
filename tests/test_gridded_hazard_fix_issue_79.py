"""Tests for issue 79 fix - gridded hazard location uniqueness."""

import json

import pytest
from graphene.test import Client

from nshm_hazard_graphql_api.schema import schema_root
from nshm_hazard_graphql_api.schema.toshi_hazard.gridded_hazard_helpers import (
    clip_tiles,
    nz_simplified_polygons,
)
from nzshm_common.grids import RegionGrid


@pytest.fixture
def graphql_client():
    yield Client(schema_root)


class TestGriddedHazardIssue79:
    """Tests for issue 79 - location uniqueness in gridded hazard."""

    @pytest.mark.skip("Test under investigation")
    def test_get_gridded_hazard_uniqueness(self, gridded_hazard_fixtures, graphql_client):

        QUERY = """
        query {
            gridded_hazard (
                grid_id: NZ_0_1_NB_1_1
                hazard_model_id: "NSHM_v1.0.4"
                imt: "PGA"
                agg: "0.5"
                vs30: 400
                poe: 0.02
            )
            {
                ok
                gridded_hazard {
                    hazard_model
                    values
                    grid_id
                    hazard_map {
                        geojson
                    }
                }
            }
        }
        """

        executed = graphql_client.execute(QUERY)
        res = executed["data"]["gridded_hazard"]
        assert res["ok"] is True

        grid = RegionGrid["NZ_0_1_NB_1_1"].load()

        assert res["gridded_hazard"][0]["grid_id"] == "NZ_0_1_NB_1_1"
        assert len(res["gridded_hazard"][0]["values"]) == len(grid)

        df_json = json.loads(res["gridded_hazard"][0]["hazard_map"]["geojson"])

        features = df_json.get("features")
        print(features[0])

        nz_parts = nz_simplified_polygons()
        new_geometry = clip_tiles(nz_parts, (None, 0))
        assert len(new_geometry) == 3402
        print(new_geometry[0])

        assert len(features) == len(new_geometry)

        locs = [tuple(f["properties"]["loc"]) for f in features]
        assert len(locs) == len(set(locs))
        print(features[0])
        assert len(features) == len(grid)
