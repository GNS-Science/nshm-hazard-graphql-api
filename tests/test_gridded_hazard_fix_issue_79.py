"""Tests for toshi_hazard_rev module."""

import unittest
import itertools
import random
import json
from unittest import mock

from graphene.test import Client
import pytest

from nshm_hazard_graphql_api.schema import schema_root
from nshm_hazard_graphql_api.schema.toshi_hazard.gridded_hazard_helpers import (
    # CustomPolygon,
    clip_tiles,
    nz_simplified_polygons,
)

from toshi_hazard_store import model
from nzshm_common.grids import RegionGrid

# log = logging.getLogger()
# logging.basicConfig(level=logging.DEBUG)
# logging.getLogger('botocore').setLevel(logging.INFO)
# logging.getLogger('pynamodb').setLevel(logging.DEBUG)
# logging.getLogger('toshi_hazard_store').setLevel(logging.DEBUG)

HAZARD_MODEL_ID = 'GRIDDED_THE_THIRD'
vs30s = [250, 400]
imts = ['PGA', 'SA(0.5)']
aggs = ['mean', '0.10']


def build_hazard_aggregation_models(*args, **kwargs):
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


def mock_query_response(*args, **kwargs):
    return list(build_hazard_aggregation_models(args, kwargs))


# query.get_one_gridded_hazard
@mock.patch(
    'nshm_hazard_graphql_api.schema.toshi_hazard.gridded_hazard.cacheable_gridded_hazard_query',
    side_effect=mock_query_response,
)
class TestGriddedHazard(unittest.TestCase):
    def setUp(self):
        self.client = Client(schema_root)

    @pytest.mark.skip('WHAT IZZZ')
    def test_get_gridded_hazard_uniqueness(self, mocked_qry):

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
                    hazard_map {
                        geojson
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

        df_json = json.loads(res['gridded_hazard'][0]['hazard_map']['geojson'])

        features = df_json.get('features')
        print(features[0])

        # should be 3402 unique locations
        nz_parts = nz_simplified_polygons()
        new_geometry = clip_tiles(nz_parts, (None, 0))
        assert len(new_geometry) == 3402
        print(new_geometry[0])

        assert 0

        self.assertEqual(len(features), len(new_geometry))

        locs = [tuple(f["properties"]["loc"]) for f in features]
        assert len(locs) == len(set(locs))
        print(features[0])
        self.assertEqual(len(features), len(grid))  # one tile dropped

        self.assertTrue(max(res['gridded_hazard'][0]['values']) < 4.7)
        self.assertTrue(max(res['gridded_hazard'][0]['values']) > 4.5)
