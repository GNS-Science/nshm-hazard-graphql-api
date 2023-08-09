"""Tests for toshi_hazard_rev module."""

import unittest
import itertools
from unittest import mock

from graphene.test import Client
from moto import mock_cloudwatch

with mock_cloudwatch():
    from nshm_hazard_graphql_api.schema import schema_root

from toshi_hazard_store import model

from nzshm_common.location import CodedLocation
from nzshm_common.location.location import LOCATIONS_BY_ID

HAZARD_MODEL_ID = 'GRIDDED_THE_THIRD'
vs30s = [250, 350, 450]
imts = ['PGA', 'SA(0.5)']
aggs = ['mean', '0.10']


wlg = LOCATIONS_BY_ID['WLG']
dud = LOCATIONS_BY_ID['DUD']
locs = [
    CodedLocation(wlg['latitude'], wlg['longitude'], 0.001),
    CodedLocation(dud['latitude'], dud['longitude'], 0.001),
]


def build_hazard_aggregation_models():

    n_lvls = 29
    lvps = list(map(lambda x: model.LevelValuePairAttribute(lvl=x / 1e3, val=(x / 1e6)), range(1, n_lvls)))
    for (loc, vs30, agg) in itertools.product(locs[:5], vs30s, aggs):
        for imt, val in enumerate(imts):
            yield model.HazardAggregation(
                values=lvps,
                vs30=vs30,
                agg=agg,
                imt=val,
                hazard_model_id=HAZARD_MODEL_ID,
            ).set_location(loc)


def mock_query_response(*args, **kwargs):
    return build_hazard_aggregation_models()


class TestResolveArbitraryLocationToGridded(unittest.TestCase):
    def setUp(self):
        self.client = Client(schema_root)

    def test_get_gridded_location(self):

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
            locs[0].lat,
            locs[0].lon,
            0.1,
        )

        executed = self.client.execute(QUERY)
        print(executed)
        res = executed['data']['gridded_location']

        self.assertEqual(res['ok'], True)

        expected = locs[0].downsample(0.1)
        self.assertEqual(res['location']['lon'], expected.lon)
        self.assertEqual(res['location']['lat'], expected.lat)
        self.assertEqual(res['location']['code'], expected.code)
        self.assertEqual(res['location']['resolution'], expected.resolution)


@mock.patch('toshi_hazard_store.query_v3.get_hazard_curves', side_effect=mock_query_response)
class TestHazardCurves(unittest.TestCase):
    def setUp(self):
        self.client = Client(schema_root)

    def test_get_hazard_for_gridded_with_key_locations(self, mocked_qry):

        QUERY = """
        query {
            hazard_curves (
                hazard_model: "%s"
                imts: ["PGA", "SA(0.5)"]
                locs: ["WLG", "DUD"]
                aggs: ["mean", "0.005", "0.995", "0.1", "0.9"]
                vs30s: [400, 250]
                resolution: 0.01
                )
            {
                ok
                curves {
                    hazard_model
                    imt
                    loc
                    agg
                    vs30
                    # curve {
                    #     levels
                    #     values
                    # }
                }
                locations {
                  lat
                  lon
                  resolution
                  code
                  name
                  key
                }
            }
        }
        """ % (
            HAZARD_MODEL_ID
        )  # , json.dumps(locs))

        executed = self.client.execute(QUERY)
        res = executed['data']['hazard_curves']

        print(executed)

        self.assertEqual(res['ok'], True)
        self.assertEqual(mocked_qry.call_count, 1)

        mocked_qry.assert_called_with(
            ["-41.300~174.780", "-45.870~170.500"],  # the resolved codes for the respective cities by ID
            [400.0, 250.0],
            ['GRIDDED_THE_THIRD'],
            ['PGA', 'SA(0.5)'],
            aggs=["mean", "0.005", "0.995", "0.1", "0.9"],
        )

        wlg = LOCATIONS_BY_ID['WLG']
        expected_res = 0.001
        expected = CodedLocation(wlg['latitude'], wlg['longitude'], expected_res)  # .resample(0.001)

        self.assertEqual(res['locations'][0]['lon'], expected.lon)
        self.assertEqual(res['locations'][0]['lat'], expected.lat)
        self.assertEqual(res['locations'][0]['code'], expected.code)
        self.assertEqual(res['locations'][0]['resolution'], expected_res)
        self.assertEqual(res['locations'][0]['name'], "Wellington")
        self.assertEqual(res['locations'][0]['key'], "WLG")
        self.assertEqual(res['curves'][0]['loc'], expected.code)

    def test_get_hazard_for_gridded_with_key_locations_lowres(self, mocked_qry):

        QUERY = """
        query {
            hazard_curves (
                hazard_model: "%s"
                imts: ["PGA", "SA(0.5)"]
                locs: ["WLG", "DUD"]
                aggs: ["mean", "0.005", "0.995", "0.1", "0.9"]
                vs30s: [400, 250]
                # resolution: 0.1 #ignot
                )
            {
                ok
                curves {
                    hazard_model
                    imt
                    loc
                    agg
                    vs30
                    # curve {
                    #     levels
                    #     values
                    # }
                }
                locations {
                  lat
                  lon
                  resolution
                  code
                  name
                  key
                }
            }
        }
        """ % (
            HAZARD_MODEL_ID
        )  # , json.dumps(locs))

        executed = self.client.execute(QUERY)
        res = executed['data']['hazard_curves']

        print(executed)

        self.assertEqual(res['ok'], True)
        self.assertEqual(mocked_qry.call_count, 1)

        mocked_qry.assert_called_with(
            ["-41.300~174.780", "-45.870~170.500"],  # the resolved codes for the respective cities by ID
            [400.0, 250.0],
            ['GRIDDED_THE_THIRD'],
            ['PGA', 'SA(0.5)'],
            aggs=["mean", "0.005", "0.995", "0.1", "0.9"],
        )

        wlg = LOCATIONS_BY_ID['WLG']
        expected_res = 0.001
        expected = CodedLocation(wlg['latitude'], wlg['longitude'], expected_res)  # .resample(0.001)

        self.assertEqual(res['locations'][0]['lon'], expected.lon)
        self.assertEqual(res['locations'][0]['lat'], expected.lat)
        self.assertEqual(res['locations'][0]['code'], expected.code)
        self.assertEqual(res['locations'][0]['resolution'], expected_res)
        self.assertEqual(res['locations'][0]['name'], "Wellington")
        self.assertEqual(res['locations'][0]['key'], "WLG")

    def test_get_wlg_by_latlon(self, mocked_qry):

        QUERY = """
        query {
            hazard_curves (
                locs: ["-41.30~174.78"]
                hazard_model: "%s"
                imts: ["PGA"]
                aggs: ["mean"]
                vs30s: [400]
                resolution: 0.01
                )
            {
                ok
                curves {
                    hazard_model
                    curve {
                        levels
                        values
                    }
                }
                locations {
                  lat
                  lon
                  resolution
                  code
                  name
                  key
                }
            }
        }
        """ % (
            HAZARD_MODEL_ID
        )  # , json.dumps(locs))

        executed = self.client.execute(QUERY)
        res = executed['data']['hazard_curves']
        print(executed)

        self.assertEqual(res['ok'], True)
        self.assertEqual(mocked_qry.call_count, 1)
        mocked_qry.assert_called_with(
            ["-41.300~174.780"],  # the resolved codes for the respective cities by ID
            [400.0],
            ['GRIDDED_THE_THIRD'],
            ['PGA'],
            aggs=["mean"],
        )

        wlg = LOCATIONS_BY_ID['WLG']
        expected_res = 0.001
        expected = CodedLocation(wlg['latitude'], wlg['longitude'], expected_res)

        self.assertEqual(res['locations'][0]['lon'], expected.lon)
        self.assertEqual(res['locations'][0]['lat'], expected.lat)
        self.assertEqual(res['locations'][0]['code'], expected.code)
        self.assertEqual(res['locations'][0]['resolution'], expected_res)
        self.assertEqual(res['locations'][0]['name'], "Wellington")
        self.assertEqual(res['locations'][0]['key'], "WLG")

    def test_get_hazard_for_gridded_with_arbitrary_locations(self, mocked_qry):

        QUERY = """
        query {
            hazard_curves (
                hazard_model: "%s"
                imts: ["PGA", "SA(0.5)"]
                locs: ["-36.959~174.8080144"]
                aggs: ["mean", "0.005", "0.995", "0.1", "0.9"]
                vs30s: [400, 250]
                )
            {
                ok
                curves {
                    hazard_model
                    imt
                    loc
                    agg
                    vs30
                    curve {
                        levels
                        values
                    }
                }
            }
        }
        """ % (
            HAZARD_MODEL_ID
        )

        executed = self.client.execute(QUERY)
        print(executed)
        res = executed['data']['hazard_curves']

        self.assertEqual(res['ok'], True)
        self.assertEqual(mocked_qry.call_count, 1)

        mocked_qry.assert_called_with(
            ['-37.000~174.800'],
            [400.0, 250.0],
            ['GRIDDED_THE_THIRD'],
            ['PGA', 'SA(0.5)'],
            aggs=["mean", "0.005", "0.995", "0.1", "0.9"],
        )
