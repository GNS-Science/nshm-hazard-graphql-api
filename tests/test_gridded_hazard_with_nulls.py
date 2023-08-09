"""Tests for toshi_hazard_rev module."""

import unittest

import json
from unittest import mock

from graphene.test import Client

from moto import mock_cloudwatch

with mock_cloudwatch():
    from nshm_hazard_graphql_api.schema import schema_root

from nzshm_common.grids import RegionGrid
from .test_gridded_hazard import build_hazard_aggregation_models

HAZARD_MODEL_ID = 'GRIDDED_THE_THIRD'
vs30s = [500]
imts = ['PGA']
aggs = ['mean']


def mock_query_response(*args, **kwargs):
    models = list(build_hazard_aggregation_models(args, kwargs))
    for nulled in [1787, 3685, 3686, 3687, 3688]:
        models[0].grid_poes[nulled] = None
    return models


# query.get_one_gridded_hazard
@mock.patch(
    'nshm_hazard_graphql_api.schema.toshi_hazard.gridded_hazard.cacheable_gridded_hazard_query',
    side_effect=mock_query_response,
)
class TestGriddedHazard(unittest.TestCase):
    def setUp(self):
        self.client = Client(schema_root)

    def test_get_gridded_hazard_values(self, mocked_qry):

        QUERY = """
        query {
            gridded_hazard (
                grid_id: NZ_0_1_NB_1_1
                hazard_model_id: "%s"
                imt: "PGA"
                agg: "mean"
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
        """ % (
            HAZARD_MODEL_ID
        )  # , json.dumps(locs))

        executed = self.client.execute(QUERY)
        # print(executed)
        res = executed['data']['gridded_hazard']
        self.assertEqual(res['ok'], True)
        self.assertEqual(mocked_qry.call_count, 1)
        self.assertEqual(res['gridded_hazard'][0]['grid_id'], "NZ_0_1_NB_1_1")
        self.assertEqual(len(res['gridded_hazard'][0]['values']), len(RegionGrid["NZ_0_1_NB_1_1"].load()))

    def test_get_gridded_hazard_geojson(self, mocked_qry):

        QUERY = """
        query {
            gridded_hazard (
                grid_id: NZ_0_1_NB_1_1
                hazard_model_id: "%s"
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
                    hazard_map( color_scale: "inferno", fill_opacity:0.5, color_scale_vmax: 0) {
                        geojson
                        colour_scale { levels hexrgbs}
                    }
                }
            }
        }
        """ % (
            HAZARD_MODEL_ID
        )  # , json.dumps(locs))

        executed = self.client.execute(QUERY)
        # print(executed)
        res = executed['data']['gridded_hazard']
        self.assertEqual(res['ok'], True)
        self.assertEqual(mocked_qry.call_count, 1)

        mocked_qry.assert_called_with(
            hazard_model_id='GRIDDED_THE_THIRD',
            location_grid_id='NZ_0_1_NB_1_1',
            vs30=400.0,
            imt='PGA',
            agg='mean',
            poe=0.02,
        )

        grid = RegionGrid['NZ_0_1_NB_1_1'].load()
        self.assertEqual(res['gridded_hazard'][0]['grid_id'], 'NZ_0_1_NB_1_1')
        self.assertEqual(len(res['gridded_hazard'][0]['values']), len(grid))

        print()
        df_json = json.loads(res['gridded_hazard'][0]['hazard_map']['geojson'])
        print(df_json.get('features')[0])
        # self.assertEqual(len(df_json.get('features')), len(grid)-5)
        self.assertTrue(max((v for v in res['gridded_hazard'][0]['values'] if v is not None), default=1) < 4.7)
        self.assertTrue(max((v for v in res['gridded_hazard'][0]['values'] if v is not None), default=1) > 4.5)

        cscale = res['gridded_hazard'][0]['hazard_map']['colour_scale']
        print(cscale)
        self.assertEqual(cscale['levels'][0], 0)
        self.assertEqual(cscale['levels'][-1], 5.0)

        self.assertEqual(cscale['hexrgbs'][0], '#000004')
        self.assertEqual(cscale['hexrgbs'][-1], '#fcffa4')
