"""Tests for toshi_hazard_rev module."""

import itertools
import pytest
from unittest import mock

from nzshm_common.location import CodedLocation
from nzshm_common.location.location import LOCATIONS_BY_ID
from toshi_hazard_store import model
import toshi_hazard_store.query


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


@pytest.fixture
def mock_query_response(*args, **kwargs):
    return build_hazard_aggregation_models()


class TestHazardCurvesNamedFrznJosef:
    def test_get_by_shortcode(self, mock_query_response, monkeypatch, graphql_client):

        mocked_qry = mock.Mock(return_value=mock_query_response)
        monkeypatch.setattr(toshi_hazard_store.query.datasets, 'get_hazard_curves', mocked_qry)

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

        executed = graphql_client.execute(QUERY)
        res = executed['data']['hazard_curves']
        print(executed)

        assert res['ok'] is True
        assert mocked_qry.call_count == 1
        mocked_qry.assert_called_with(
            ["-43.376~170.188"],  # the resolved codes for the respective cities by ID
            [400],
            [HAZARD_MODEL_ID],
            ['PGA'],
            aggs=["mean"],
        )

    # TODO this will be deprecated
    def test_get_wlg_by_shortcode_with_lowres(self, mock_query_response, monkeypatch, graphql_client):
        """For name location resolution is ignored. they always use 0.01"""

        mocked_qry = mock.Mock(return_value=mock_query_response)
        monkeypatch.setattr(toshi_hazard_store.query.datasets, 'get_hazard_curves', mocked_qry)

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

        executed = graphql_client.execute(QUERY)
        res = executed['data']['hazard_curves']
        print(executed)

        assert res['ok'] is True
        assert mocked_qry.call_count == 1
        mocked_qry.assert_called_with(
            ["-43.376~170.188"],  # the resolved codes for the respective cities by ID
            [400],
            [HAZARD_MODEL_ID],
            ['PGA'],
            aggs=["mean"],
        )

    def test_get_franz_josef_by_latlon(self, mock_query_response, monkeypatch, graphql_client):

        mocked_qry = mock.Mock(return_value=mock_query_response)
        monkeypatch.setattr(toshi_hazard_store.query.datasets, 'get_hazard_curves', mocked_qry)

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

        executed = graphql_client.execute(QUERY)
        res = executed['data']['hazard_curves']
        print(executed)

        assert res['ok'] is True
        assert mocked_qry.call_count == 1
        mocked_qry.assert_called_with(
            ["-43.376~170.188"],  # the resolved codes for the respective cities by ID
            [400],
            [HAZARD_MODEL_ID],
            ['PGA'],
            aggs=["mean"],
        )

    def test_get_franz_josef_by_latlon_default_resolution(self, mock_query_response, monkeypatch, graphql_client):

        mocked_qry = mock.Mock(return_value=mock_query_response)
        monkeypatch.setattr(toshi_hazard_store.query.datasets, 'get_hazard_curves', mocked_qry)

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

        executed = graphql_client.execute(QUERY)
        res = executed['data']['hazard_curves']
        print(executed)

        assert res['ok'] is True
        assert mocked_qry.call_count == 1
        mocked_qry.assert_called_with(
            ["-43.376~170.188"],  # the resolved codes for the respective cities by ID
            [400],
            [HAZARD_MODEL_ID],
            ['PGA'],
            aggs=["mean"],
        )

    def test_get_franz_josef_by_latlon_low_hazard_resolution(self, mock_query_response, monkeypatch, graphql_client):

        mocked_qry = mock.Mock(return_value=mock_query_response)
        monkeypatch.setattr(toshi_hazard_store.query.datasets, 'get_hazard_curves', mocked_qry)

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

        executed = graphql_client.execute(QUERY)
        res = executed['data']['hazard_curves']
        print(executed)

        assert res['ok'] is True
        assert mocked_qry.call_count == 1
        mocked_qry.assert_called_with(
            ["-43.376~170.188"], [400], HAZARD_MODEL_ID, ['PGA'], aggs=["mean"], strategy='d2'
        )
