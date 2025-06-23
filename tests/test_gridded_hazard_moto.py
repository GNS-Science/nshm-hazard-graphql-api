"""Tests for toshi_hazard_rev module."""

import unittest
import itertools
import random
from moto import mock_dynamodb

from graphene.test import Client

from nshm_hazard_graphql_api.schema import schema_root

from nzshm_common.grids import RegionGrid
from toshi_hazard_store import model

HAZARD_MODEL_ID = 'GRIDDED_THE_THIRD'
GRID_ID = "WLG_0_01_nb_1_1"
vs30s = [250, 400]
imts = ['PGA', 'SA(0.5)']
aggs = ['mean', '0.1']


def build_gridded_hazard_models(**kwargs):
    grid_id = GRID_ID

    region_grid = RegionGrid[grid_id]
    grid = region_grid.load()
    grid_poes = [random.randint(0, int(4.7e6)) / 1e6 for x in range(len(grid))]
    grid_poes[0] = 0.1

    for (imt, vs30, agg) in itertools.product(imts, vs30s, aggs):

        obj = model.GriddedHazard.new_model(
            hazard_model_id=HAZARD_MODEL_ID,
            location_grid_id=grid_id,
            vs30=vs30,
            imt=imt,
            agg=agg,
            poe=0.02,
            grid_poes=grid_poes,
        )
        # print('OBJ', obj)
        yield obj


@mock_dynamodb
class TestGriddedHazard(unittest.TestCase):
    def setUp(self):
        self.client = Client(schema_root)
        model.migrate()
        for m in build_gridded_hazard_models(vs30s=vs30s, imts=imts, aggs=aggs):
            m.save()
        super(TestGriddedHazard, self).setUp()

    def tearDown(self):
        model.drop_tables()
        return super(TestGriddedHazard, self).tearDown()

    def test_get_gridded_hazard_values(self):

        QUERY = """
        query {
            gridded_hazard (
                grid_id: %s
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
            GRID_ID,
            HAZARD_MODEL_ID,
        )  # , json.dumps(locs))

        print("QUERY", QUERY)
        executed = self.client.execute(QUERY)
        print('EXEC', executed)
        res = executed['data']['gridded_hazard']
        self.assertEqual(res['ok'], True)
        self.assertEqual(res['gridded_hazard'][0]['grid_id'], "WLG_0_01_nb_1_1")
        self.assertEqual(len(res['gridded_hazard'][0]['values']), 764)

    def test_get_gridded_hazard_geojson(self):

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
        )

        executed = self.client.execute(QUERY)
        # print(executed)
        res = executed['data']['gridded_hazard']
        self.assertEqual(res['ok'], True)

        self.assertEqual(res['gridded_hazard'][0]['grid_id'], 'WLG_0_01_nb_1_1')
        self.assertEqual(len(res['gridded_hazard'][0]['values']), 764)

    @unittest.skip('deprecated')
    def test_kororaa_query(self):

        QUERY = """
        query HazardMapsPageQuery($grid_id: RegionGrid, $hazard_model_ids: [String], $imts: [String],
            $aggs: [String], $vs30s: [Float],
            $poes: [Float], $color_scale: String,
            $color_scale_vmax: Float, $fill_opacity: Float, $stroke_width: Float, $stroke_opacity: Float) {
          gridded_hazard(grid_id: $grid_id, hazard_model_ids: $hazard_model_ids, imts: $imts, aggs: $aggs,
            vs30s: $vs30s, poes: $poes) {
                ok
                gridded_hazard {
                  grid_id
                  hazard_model
                  imt
                  agg
                  values
                  hazard_map(color_scale: $color_scale, color_scale_vmax: $color_scale_vmax,
                    fill_opacity: $fill_opacity, stroke_width: $stroke_width, stroke_opacity: $stroke_opacity,
                    color_scale_normalise:LOG) {
                    geojson
                    colour_scale {
                      levels
                      hexrgbs
                    }
                  }
                }
            }
        }
        """

        args = {
            "hazard_model_ids": [HAZARD_MODEL_ID],
            "grid_id": GRID_ID,
            "vs30s": [400],
            "imts": ["PGA"],
            "aggs": ["mean"],
            "poes": [0.02],
            "color_scale": "inferno",
            "color_scale_vmax": 0,
            "fill_opacity": 0.5,
            "stroke_opacity": 0.5,
            "stroke_width": 0.1,
        }
        executed = self.client.execute(QUERY, variable_values=args)
        print('EXEC', executed)
        res = executed['data']['gridded_hazard']
        self.assertEqual(res['gridded_hazard'][0]['grid_id'], 'WLG_0_01_nb_1_1')
        self.assertEqual(len(res['gridded_hazard'][0]['values']), 764)
