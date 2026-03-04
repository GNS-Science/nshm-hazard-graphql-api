"""Tests for gridded hazard with null values using parquet fixtures."""

import json

import pytest
from graphene.test import Client

from nshm_hazard_graphql_api.schema import schema_root
from nzshm_common.grids import RegionGrid


@pytest.fixture
def graphql_client():
    yield Client(schema_root)


class TestGriddedHazardWithNulls:
    """Tests handling of null values in gridded hazard data."""

    def test_get_gridded_hazard_values(self, gridded_hazard_fixtures, graphql_client):

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
                    grid_id
                    values
                }
            }
        }
        """

        executed = graphql_client.execute(QUERY)
        res = executed["data"]["gridded_hazard"]
        assert res["ok"] is True
        assert res["gridded_hazard"][0]["grid_id"] == "NZ_0_1_NB_1_1"
        assert len(res["gridded_hazard"][0]["values"]) == len(RegionGrid["NZ_0_1_NB_1_1"].load())

    def test_get_gridded_hazard_geojson(self, gridded_hazard_fixtures, graphql_client):

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
                    hazard_map(color_scale: "inferno", fill_opacity: 0.5, color_scale_vmax: 0) {
                        geojson
                        colour_scale { levels hexrgbs }
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
        assert len(df_json.get("features")) > 0

        values = res["gridded_hazard"][0]["values"]
        non_null_values = [v for v in values if v is not None]
        if non_null_values:
            assert max(non_null_values) >= 0

        cscale = res["gridded_hazard"][0]["hazard_map"]["colour_scale"]
        assert cscale["levels"][0] == 0
