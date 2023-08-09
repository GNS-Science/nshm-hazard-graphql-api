"""Tests for toshi_hazard_rev module."""

import unittest

from unittest import mock

from graphene.test import Client
from moto import mock_cloudwatch

with mock_cloudwatch():
    from nshm_hazard_graphql_api.schema import schema_root

HAZARD_MODEL_ID = 'GRIDDED_THE_THIRD'
# vs30s = [250, 350, 450]
# imts = ['PGA', 'SA(0.5)']
# aggs = ['mean', '0.10']


@mock.patch('toshi_hazard_store.query_v3.get_hazard_curves')
class TestHazardCurvesNamed(unittest.TestCase):
    def setUp(self):
        self.client = Client(schema_root)

    def test_get_wlg_by_shortcode(self, mocked_qry):

        QUERY = """
        query {
            hazard_curves (
                locs: ["WLG"]
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
            ["-41.300~174.780"],  # the resolved codes for the respective cities by ID
            [400.0],
            ['GRIDDED_THE_THIRD'],
            ['PGA'],
            aggs=["mean"],
        )

    def test_get_wlg_by_shortcode_with_lowres(self, mocked_qry):
        """For name location resolution is ignored. they always use 0.01"""

        QUERY = """
        query {
            hazard_curves (
                locs: ["WLG"]
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
            ["-41.300~174.780"],  # the resolved codes for the respective cities by ID
            [400.0],
            ['GRIDDED_THE_THIRD'],
            ['PGA'],
            aggs=["mean"],
        )

    def test_get_wlg_by_latlon(self, mocked_qry):

        QUERY = """
        query {
            hazard_curves (
                locs: ["-41.30~174.78"]
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
            ["-41.300~174.780"],  # the resolved codes for the respective cities by ID
            [400.0],
            ['GRIDDED_THE_THIRD'],
            ['PGA'],
            aggs=["mean"],
        )

    def test_get_wlg_by_latlon_low_res(self, mocked_qry):
        """For name location resolution is ignored. they always use 0.01"""
        QUERY = """
        query {
            hazard_curves (
                locs: ["-41.30~174.78"]
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
            ["-41.300~174.780"],  # the resolved codes for the respective cities by ID
            [400.0],
            ['GRIDDED_THE_THIRD'],
            ['PGA'],
            aggs=["mean"],
        )
