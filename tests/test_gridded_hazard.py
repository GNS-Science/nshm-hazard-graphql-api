"""Tests for toshi_hazard_rev module."""

import unittest
import itertools
import random
import json
from unittest import mock

from graphene.test import Client

# from moto import mock_cloudwatch

# with mock_cloudwatch():
from nshm_hazard_graphql_api.schema import schema_root

from toshi_hazard_store import model
from nzshm_common.grids import RegionGrid

# import nshm_hazard_graphql_api.schema.toshi_hazard.gridded_hazard

# log = logging.getLogger()
# logging.basicConfig(level=logging.DEBUG)
# logging.getLogger('botocore').setLevel(logging.INFO)
# logging.getLogger('pynamodb').setLevel(logging.DEBUG)
# logging.getLogger('toshi_hazard_store').setLevel(logging.DEBUG)

HAZARD_MODEL_ID = 'GRIDDED_THE_THIRD'
vs30s = [250, 400]
imts = ['PGA', 'SA(0.5)']
aggs = ['mean', '0.10']


def build_hazard_gridded_models(*args, **kwargs):
    print('args', args)
    grid_id = args[1]['location_grid_id']
    grid = RegionGrid[grid_id].load()

    grid_poes = [random.randint(0, int(4.7e6)) / int(1e6) for x in range(len(grid))]
    grid_poes[0] = 0.1

    for (imt, vs30, agg) in itertools.product(imts, vs30s, aggs):

        obj = model.GriddedHazard.new_model(
            hazard_model_id=args[1]['hazard_model_id'],
            location_grid_id=grid_id,
            vs30=vs30,
            imt=imt,
            agg=agg,
            poe=0.02,
            grid_poes=grid_poes,
        )
        # print('OBJ', obj)
        yield obj


def mock_gridded_query_response(*args, **kwargs):
    return list(build_hazard_gridded_models(args, kwargs))


# query.get_one_gridded_hazard
@mock.patch(
    'nshm_hazard_graphql_api.schema.toshi_hazard.gridded_hazard.cacheable_gridded_hazard_query',
    side_effect=mock_gridded_query_response,
)
class TestGriddedHazard(unittest.TestCase):
    def setUp(self):
        self.client = Client(schema_root)

    def test_get_gridded_hazard_values(self, mocked_qry):

        QUERY = """
        query {
            gridded_hazard (
                grid_id: WLG_0_01_nb_1_1
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

        # mocked_qry.assert_called_with(
        #     hazard_model_ids=['GRIDDED_THE_THIRD'],
        #     location_grid_ids=['WLG_0_01_nb_1_1'],
        #     vs30s=[400.0, 250.0],
        #     imts=['PGA', 'SA(0.5)'],
        #     aggs=['mean', '0.9'],
        #     poes=[0.1, 0.02],
        # )

        self.assertEqual(res['gridded_hazard'][0]['grid_id'], "WLG_0_01_nb_1_1")
        self.assertEqual(len(res['gridded_hazard'][0]['values']), 764)

    def test_get_gridded_hazard_geojson(self, mocked_qry):

        QUERY = """
        query {
            gridded_hazard (
                grid_id: WLG_0_01_nb_1_1
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
            location_grid_id='WLG_0_01_nb_1_1',
            vs30=400.0,
            imt='PGA',
            agg='mean',
            poe=0.02,
        )

        self.assertEqual(res['gridded_hazard'][0]['grid_id'], 'WLG_0_01_nb_1_1')
        self.assertEqual(len(res['gridded_hazard'][0]['values']), 764)

        print()
        df_json = json.loads(res['gridded_hazard'][0]['hazard_map']['geojson'])
        print(df_json.get('features')[0])
        self.assertEqual(len(df_json.get('features')), 763)  # one tile dropped
        self.assertTrue(max(res['gridded_hazard'][0]['values']) < 4.7)
        self.assertTrue(max(res['gridded_hazard'][0]['values']) > 4.5)

        cscale = res['gridded_hazard'][0]['hazard_map']['colour_scale']
        print(cscale)
        self.assertEqual(cscale['levels'][0], 0)
        self.assertEqual(cscale['levels'][-1], 5.0)

        self.assertEqual(cscale['hexrgbs'][0], '#000004')
        self.assertEqual(cscale['hexrgbs'][-1], '#fcffa4')

    def test_get_gridded_hazard_auto_vmax_0(self, mocked_qry):

        QUERY = """
        query {
            gridded_hazard (
                grid_id: WLG_0_01_nb_1_1
                hazard_model_id: "%s"
                imt: "PGA"
                agg: "mean"
                vs30: 400
                poe: 0.02
                )
            {
                ok
                gridded_hazard {
                    hazard_map( color_scale: "inferno", color_scale_vmax: 0) {
                        colour_scale { levels hexrgbs}
                    }
                }
            }
        }
        """ % (
            HAZARD_MODEL_ID
        )  # , json.dumps(locs))

        executed = self.client.execute(QUERY)
        print(executed)
        res = executed['data']['gridded_hazard']
        cscale = res['gridded_hazard'][0]['hazard_map']['colour_scale']
        self.assertEqual(cscale['levels'][-1], 5.0)

    def test_get_gridded_hazard_auto_vmax_none(self, mocked_qry):

        QUERY = """
        query {
            gridded_hazard (
                grid_id: WLG_0_01_nb_1_1
                hazard_model_id: "%s"
                imt: "PGA"
                agg: "mean"
                vs30: 400
                poe: 0.02
                )
            {
                ok
                gridded_hazard {
                    hazard_map( color_scale: "inferno") {
                        colour_scale { levels hexrgbs}
                    }
                }
            }
        }
        """ % (
            HAZARD_MODEL_ID
        )  # , json.dumps(locs))

        executed = self.client.execute(QUERY)
        print(executed)
        res = executed['data']['gridded_hazard']
        cscale = res['gridded_hazard'][0]['hazard_map']['colour_scale']
        self.assertEqual(cscale['levels'][-1], 5.0)

    def test_get_gridded_hazard_manual_vmax(self, mocked_qry):

        QUERY = """
        query {
            gridded_hazard (
                grid_id: WLG_0_01_nb_1_1
                hazard_model_id: "%s"
                imt: "PGA"
                agg: "mean"
                vs30: 400
                poe: 0.02
            )
            {
                ok
                gridded_hazard {
                    hazard_map( color_scale_vmax: 6.5 ) {
                        colour_scale { levels hexrgbs}
                    }
                }
            }
        }
        """ % (
            HAZARD_MODEL_ID
        )  # , json.dumps(locs))

        executed = self.client.execute(QUERY)
        print(executed)
        res = executed['data']['gridded_hazard']
        cscale = res['gridded_hazard'][0]['hazard_map']['colour_scale']
        self.assertEqual(cscale['levels'][-1], 6.5)

    def test_get_gridded_hazard_color_scale_log(self, mocked_qry):

        QUERY = """
        query {
            gridded_hazard (
                grid_id: WLG_0_01_nb_1_1
                hazard_model_id: "%s"
                imt: "PGA"
                agg: "mean"
                vs30: 400
                poe: 0.02
            )
            {
                ok
                gridded_hazard {
                    hazard_map (color_scale_normalise: LOG) {
                        colour_scale { levels hexrgbs}
                    }
                }
            }
        }
        """ % (
            HAZARD_MODEL_ID
        )  # , json.dumps(locs))

        executed = self.client.execute(QUERY)
        print(executed)
        res = executed['data']['gridded_hazard']
        cscale = res['gridded_hazard'][0]['hazard_map']['colour_scale']
        print(cscale)
        self.assertEqual(cscale['levels'][0], 0)
        self.assertEqual(cscale['levels'][-1], 5.0)

        self.assertEqual(cscale['hexrgbs'][0], '#000000')
        # self.assertEqual(cscale['hexrgbs'][1], '#46ffb1') # too much random
        # self.assertEqual(cscale['hexrgbs'][-4], '#890000')
        self.assertEqual(cscale['hexrgbs'][-1], '#800000')


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
        print(executed)
        res = executed['data']['gridded_location']

        assert res['ok'] is True

        expected = locations[0].downsample(0.1)
        assert res['location']['lon'] == expected.lon
        assert res['location']['lat'] == expected.lat
        assert res['location']['code'] == expected.code
        assert res['location']['resolution'] == expected.resolution
