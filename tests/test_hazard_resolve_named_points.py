"""Tests for toshi_hazard_rev module."""

from unittest import mock

import toshi_hazard_store.query.hazard_query
import nshm_hazard_graphql_api.schema.toshi_hazard.hazard_curves

HAZARD_MODEL_ID = 'GRIDDED_THE_THIRD'


class TestHazardCurvesNamed:
    def test_get_wlg_by_shortcode(self, mock_query_response, monkeypatch, graphql_client):

        mocked_qry = mock.Mock(return_value=mock_query_response)
        monkeypatch.setattr(toshi_hazard_store.query.hazard_query, 'get_hazard_curves', mocked_qry)
        monkeypatch.setattr(nshm_hazard_graphql_api.schema.toshi_hazard.hazard_curves, 'DATASET_AGGR_ENABLED', False)

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

        executed = graphql_client.execute(QUERY)
        res = executed['data']['hazard_curves']
        print(executed)

        assert res['ok'] is True
        assert mocked_qry.call_count == 1
        assert mocked_qry.called_with(
            ["-41.300~174.780"],  # the resolved codes for the respective cities by ID
            [400.0],
            ['GRIDDED_THE_THIRD'],
            ['PGA'],
            aggs=["mean"],
        )

    def test_get_wlg_by_shortcode_with_lowres(self, mock_query_response, monkeypatch, graphql_client):
        """For name location resolution is ignored. they always use 0.01"""

        mocked_qry = mock.Mock(return_value=mock_query_response)
        monkeypatch.setattr(toshi_hazard_store.query.hazard_query, 'get_hazard_curves', mocked_qry)
        monkeypatch.setattr(nshm_hazard_graphql_api.schema.toshi_hazard.hazard_curves, 'DATASET_AGGR_ENABLED', False)

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

        executed = graphql_client.execute(QUERY)
        res = executed['data']['hazard_curves']
        print(executed)

        assert res['ok'] is True
        assert mocked_qry.call_count == 1
        assert mocked_qry.called_with(
            ["-41.300~174.780"],  # the resolved codes for the respective cities by ID
            [400.0],
            ['GRIDDED_THE_THIRD'],
            ['PGA'],
            aggs=["mean"],
        )

    def test_get_wlg_by_latlon(self, mock_query_response, monkeypatch, graphql_client):

        mocked_qry = mock.Mock(return_value=mock_query_response)
        monkeypatch.setattr(toshi_hazard_store.query.hazard_query, 'get_hazard_curves', mocked_qry)
        monkeypatch.setattr(nshm_hazard_graphql_api.schema.toshi_hazard.hazard_curves, 'DATASET_AGGR_ENABLED', False)

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

        executed = graphql_client.execute(QUERY)
        res = executed['data']['hazard_curves']
        print(executed)

        assert res['ok'] is True
        assert mocked_qry.call_count == 1
        assert mocked_qry.called_with(
            ["-41.300~174.780"],  # the resolved codes for the respective cities by ID
            [400.0],
            ['GRIDDED_THE_THIRD'],
            ['PGA'],
            aggs=["mean"],
        )

    def test_get_wlg_by_latlon_low_res(self, mock_query_response, monkeypatch, graphql_client):
        """For name location resolution is ignored. they always use 0.01"""

        mocked_qry = mock.Mock(return_value=mock_query_response)
        monkeypatch.setattr(toshi_hazard_store.query.hazard_query, 'get_hazard_curves', mocked_qry)
        monkeypatch.setattr(nshm_hazard_graphql_api.schema.toshi_hazard.hazard_curves, 'DATASET_AGGR_ENABLED', False)

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

        executed = graphql_client.execute(QUERY)
        res = executed['data']['hazard_curves']
        print(executed)

        assert res['ok'] is True
        assert mocked_qry.call_count == 1
        assert mocked_qry.called_with(
            ["-41.300~174.780"],  # the resolved codes for the respective cities by ID
            [400.0],
            ['GRIDDED_THE_THIRD'],
            ['PGA'],
            aggs=["mean"],
        )
