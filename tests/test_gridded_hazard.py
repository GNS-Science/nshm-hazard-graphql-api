"""Tests for gridded hazard query using parquet fixtures."""

import json

import pytest
from graphene.test import Client

from nshm_hazard_graphql_api.schema import schema_root

HAZARD_MODEL_ID = "NSHM_v1.0.4"
GRID_ID = "NZ_0_1_NB_1_1"


@pytest.fixture
def graphql_client():
    yield Client(schema_root)


class TestGriddedHazard:
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

    def test_get_gridded_hazard_geojson(self, gridded_hazard_fixtures, graphql_client):

        QUERY = """
        query {
            gridded_hazard (
                grid_id: NZ_0_1_NB_1_1
                hazard_model_id: "NSHM_v1.0.4"
                imt: "PGA"
                agg: "mean"
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
        assert res["gridded_hazard"][0]["grid_id"] == "NZ_0_1_NB_1_1"

        df_json = json.loads(res["gridded_hazard"][0]["hazard_map"]["geojson"])
        assert len(df_json.get("features")) > 0

        cscale = res["gridded_hazard"][0]["hazard_map"]["colour_scale"]
        assert cscale["levels"][0] == 0

    def test_get_gridded_hazard_auto_vmax_0(self, gridded_hazard_fixtures, graphql_client):

        QUERY = """
        query {
            gridded_hazard (
                grid_id: NZ_0_1_NB_1_1
                hazard_model_id: "NSHM_v1.0.4"
                imt: "PGA"
                agg: "mean"
                vs30: 400
                poe: 0.02
            )
            {
                ok
                gridded_hazard {
                    hazard_map(color_scale: "inferno", color_scale_vmax: 0) {
                        colour_scale { levels hexrgbs }
                    }
                }
            }
        }
        """

        executed = graphql_client.execute(QUERY)
        res = executed["data"]["gridded_hazard"]
        assert res["ok"] is True
        cscale = res["gridded_hazard"][0]["hazard_map"]["colour_scale"]
        assert cscale["levels"][-1] >= 0

    def test_get_gridded_hazard_auto_vmax_none(self, gridded_hazard_fixtures, graphql_client):

        QUERY = """
        query {
            gridded_hazard (
                grid_id: NZ_0_1_NB_1_1
                hazard_model_id: "NSHM_v1.0.4"
                imt: "PGA"
                agg: "mean"
                vs30: 400
                poe: 0.02
            )
            {
                ok
                gridded_hazard {
                    hazard_map(color_scale: "inferno") {
                        colour_scale { levels hexrgbs }
                    }
                }
            }
        }
        """

        executed = graphql_client.execute(QUERY)
        res = executed["data"]["gridded_hazard"]
        assert res["ok"] is True
        cscale = res["gridded_hazard"][0]["hazard_map"]["colour_scale"]
        assert cscale["levels"][-1] >= 0

    def test_get_gridded_hazard_manual_vmax(self, gridded_hazard_fixtures, graphql_client):

        QUERY = """
        query {
            gridded_hazard (
                grid_id: NZ_0_1_NB_1_1
                hazard_model_id: "NSHM_v1.0.4"
                imt: "PGA"
                agg: "mean"
                vs30: 400
                poe: 0.02
            )
            {
                ok
                gridded_hazard {
                    hazard_map(color_scale_vmax: 6.5) {
                        colour_scale { levels hexrgbs }
                    }
                }
            }
        }
        """

        executed = graphql_client.execute(QUERY)
        res = executed["data"]["gridded_hazard"]
        assert res["ok"] is True
        cscale = res["gridded_hazard"][0]["hazard_map"]["colour_scale"]
        assert cscale["levels"][-1] == 6.5

    def test_get_gridded_hazard_color_scale_log(self, gridded_hazard_fixtures, graphql_client):

        QUERY = """
        query {
            gridded_hazard (
                grid_id: NZ_0_1_NB_1_1
                hazard_model_id: "NSHM_v1.0.4"
                imt: "PGA"
                agg: "mean"
                vs30: 400
                poe: 0.02
            )
            {
                ok
                gridded_hazard {
                    hazard_map(color_scale_normalise: LOG) {
                        colour_scale { levels hexrgbs }
                    }
                }
            }
        }
        """

        executed = graphql_client.execute(QUERY)
        res = executed["data"]["gridded_hazard"]
        assert res["ok"] is True
        cscale = res["gridded_hazard"][0]["hazard_map"]["colour_scale"]
        assert cscale["levels"][0] == 0
        assert cscale["levels"][-1] >= 0


class TestResolveArbitraryLocationToGridded:
    def test_get_gridded_location_with_off_grid_location(self, graphql_client, locations):
        """No mocking required."""

        QUERY = """
        query {
            gridded_location (
                lat: %s
                lon: %s
                resolution: %s
            )
            {
                ok
                location {
                    lat
                    lon
                    code
                    resolution
                }
            }
        }
        """ % (
            locations[0].lat,
            locations[0].lon,
            0.1,
        )

        executed = graphql_client.execute(QUERY)
        res = executed["data"]["gridded_location"]

        assert res["ok"] is True

        expected = locations[0].downsample(0.1)
        assert res["location"]["lon"] == expected.lon
        assert res["location"]["lat"] == expected.lat
        assert res["location"]["code"] == expected.code
        assert res["location"]["resolution"] == expected.resolution
