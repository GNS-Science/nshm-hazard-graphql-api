"""Tests for toshi_hazard_rev module."""

import unittest
import itertools

from unittest import mock

from graphene.test import Client
from moto import mock_cloudwatch

with mock_cloudwatch():
    from nshm_hazard_graphql_api.schema import schema_root

from nzshm_common.location import CodedLocation
from nzshm_common.location.location import LOCATIONS_BY_ID
from toshi_hazard_store import model

HAZARD_MODEL_ID = 'GRIDDED_THE_NINTH'
vs30s = [400]
imts = ['PGA']
aggs = ['mean']

who = LOCATIONS_BY_ID['WHO']
srg_164 = LOCATIONS_BY_ID['srg_164']
locs = [
    CodedLocation(who['latitude'], who['longitude'], 0.001),
    CodedLocation(srg_164['latitude'], srg_164['longitude'], 0.001),
    CodedLocation(-43.4, 170.2, 0.001),
]


def build_hazard_aggregation_models():
    n_lvls = 29
    lvps = list(map(lambda x: model.LevelValuePairAttribute(lvl=x / 1e3, val=(x / 1e6)), range(1, n_lvls)))
    for (loc, vs30, agg) in itertools.product(locs, vs30s, aggs):
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


@mock.patch('toshi_hazard_store.query_v3.get_hazard_curves', side_effect=mock_query_response)
class TestHazardCurvesNamed(unittest.TestCase):
    def setUp(self):
        self.client = Client(schema_root)

    def test_get_by_shortcode(self, mocked_qry):

        QUERY = """
        query {
            hazard_curves (
                locs: ["srg_164"]
                hazard_model: "%s"
                imts: ["PGA"]
                aggs: ["mean"]
                vs30s: [400]
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
            ["-43.376~170.188"],  # the resolved codes for the respective cities by ID
            [400],
            [HAZARD_MODEL_ID],
            ['PGA'],
            aggs=["mean"],
        )

    # TODO this will be deprecated
    def test_get_wlg_by_shortcode_with_lowres(self, mocked_qry):
        """For name location resolution is ignored. they always use 0.01"""

        QUERY = """
        query {
            hazard_curves (
                locs: ["srg_164"]
                hazard_model: "%s"
                imts: ["PGA"]
                aggs: ["mean"]
                vs30s: [400]
                resolution: 0.1
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
            ["-43.376~170.188"],  # the resolved codes for the respective cities by ID
            [400],
            [HAZARD_MODEL_ID],
            ['PGA'],
            aggs=["mean"],
        )

    def test_get_franz_josef_by_latlon(self, mocked_qry):
        QUERY = """
        query {
            hazard_curves (
                locs: ["-43.376~170.188"]
                hazard_model: "%s"
                imts: ["PGA"]
                aggs: ["mean"]
                vs30s: [400]
                resolution: 0.001
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
            ["-43.376~170.188"],  # the resolved codes for the respective cities by ID
            [400],
            [HAZARD_MODEL_ID],
            ['PGA'],
            aggs=["mean"],
        )

    def test_get_franz_josef_by_latlon_default_resolution(self, mocked_qry):
        QUERY = """
        query {
            hazard_curves (
                locs: ["-43.376~170.188"]
                hazard_model: "%s"
                imts: ["PGA"]
                aggs: ["mean"]
                vs30s: [400]
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
            ["-43.376~170.188"],  # the resolved codes for the respective cities by ID
            [400],
            [HAZARD_MODEL_ID],
            ['PGA'],
            aggs=["mean"],
        )

    def test_get_franz_josef_by_latlon_low_hazard_resolution(self, mocked_qry):
        QUERY = """
        query {
            hazard_curves (
                locs: ["-43.376~170.188"]
                hazard_model: "%s"
                imts: ["PGA"]
                aggs: ["mean"]
                vs30s: [400]
                resolution: 0.1
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
            ["-43.376~170.188"],
            [400],
            [HAZARD_MODEL_ID],
            ['PGA'],
            aggs=["mean"],
        )
