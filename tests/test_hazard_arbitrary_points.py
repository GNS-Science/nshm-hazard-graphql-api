"""Tests for toshi_hazard_rev module."""

from unittest import mock

from nzshm_common.location import CodedLocation
from nzshm_common.location.location import LOCATIONS_BY_ID

import toshi_hazard_store.query.hazard_query

import nshm_hazard_graphql_api.schema.toshi_hazard.datasets
import nshm_hazard_graphql_api.schema.toshi_hazard.hazard_curves


class TestHazardCurves:
    def test_get_hazard_curves_with_key_locations(self, mock_query_response, monkeypatch, graphql_client):

        mocked_qry = mock.Mock(return_value=mock_query_response)
        # monkeypatch.setattr(toshi_hazard_store.query.hazard_query, 'get_hazard_curves', mocked_qry)
        monkeypatch.setattr(nshm_hazard_graphql_api.schema.toshi_hazard.datasets, 'get_hazard_curves', mocked_qry)
        # monkeypatch.setattr(nshm_hazard_graphql_api.schema.toshi_hazard.hazard_curves, 'DATASET_AGGR_ENABLED', False)

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
            "GRIDDED_THE_THIRD"
        )  # , json.dumps(locs))

        executed = graphql_client.execute(QUERY)
        res = executed['data']['hazard_curves']

        print(executed)

        assert res['ok'] is True

        assert mocked_qry.called is True
        assert mocked_qry.call_count == 1

        mocked_qry.assert_called_with(
            ["-41.300~174.780", "-45.870~170.500"],  # the resolved codes for the respective cities by ID
            [400, 250],
            'GRIDDED_THE_THIRD',
            ['PGA', 'SA(0.5)'],
            aggs=["mean", "0.005", "0.995", "0.1", "0.9"],
            strategy='d2',
        )

        wlg = LOCATIONS_BY_ID['WLG']
        expected_res = 0.001
        expected = CodedLocation(wlg['latitude'], wlg['longitude'], expected_res)  # .resample(0.001)

        assert res['locations'][0]['lon'] == expected.lon
        assert res['locations'][0]['lat'] == expected.lat
        assert res['locations'][0]['code'] == expected.code
        assert res['locations'][0]['resolution'] == expected_res
        assert res['locations'][0]['name'] == "Wellington"
        assert res['locations'][0]['key'] == "WLG"
        assert res['curves'][0]['loc'] == expected.code

    def test_get_hazard_curves_with_key_locations_lowres(self, mock_query_response, monkeypatch, graphql_client):

        mocked_qry = mock.Mock(return_value=mock_query_response)
        monkeypatch.setattr(nshm_hazard_graphql_api.schema.toshi_hazard.datasets, 'get_hazard_curves', mocked_qry)

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
            "GRIDDED_THE_THIRD"
        )  # , json.dumps(locs))

        executed = graphql_client.execute(QUERY)
        res = executed['data']['hazard_curves']

        print(executed)

        assert res['ok'] is True
        assert mocked_qry.call_count == 1

        mocked_qry.assert_called_with(
            ["-41.300~174.780", "-45.870~170.500"],  # the resolved codes for the respective cities by ID
            [400, 250],
            'GRIDDED_THE_THIRD',
            ['PGA', 'SA(0.5)'],
            aggs=["mean", "0.005", "0.995", "0.1", "0.9"],
            strategy='d2',
        )

        wlg = LOCATIONS_BY_ID['WLG']
        expected_res = 0.001
        expected = CodedLocation(wlg['latitude'], wlg['longitude'], expected_res)  # .resample(0.001)

        assert res['locations'][0]['lon'] == expected.lon
        assert res['locations'][0]['lat'] == expected.lat
        assert res['locations'][0]['code'] == expected.code
        assert res['locations'][0]['resolution'] == expected_res
        assert res['locations'][0]['name'] == "Wellington"
        assert res['locations'][0]['key'] == "WLG"

    def test_get_wlg_by_latlon(self, mock_query_response, monkeypatch, graphql_client):

        mocked_qry = mock.Mock(return_value=mock_query_response)
        monkeypatch.setattr(nshm_hazard_graphql_api.schema.toshi_hazard.datasets, 'get_hazard_curves', mocked_qry)

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
            "HAZARD_THE_THIRD"
        )  # , json.dumps(locs))

        executed = graphql_client.execute(QUERY)
        res = executed['data']['hazard_curves']
        print(executed)

        assert res['ok'] is True
        assert mocked_qry.call_count == 1
        mocked_qry.assert_called_with(
            ["-41.300~174.780"],  # the resolved codes for the respective cities by ID
            [400],
            'HAZARD_THE_THIRD',
            ['PGA'],
            aggs=["mean"],
            strategy='d2',
        )

        wlg = LOCATIONS_BY_ID['WLG']
        expected_res = 0.001
        expected = CodedLocation(wlg['latitude'], wlg['longitude'], expected_res)

        assert res['locations'][0]['lon'] == expected.lon
        assert res['locations'][0]['lat'] == expected.lat
        assert res['locations'][0]['code'] == expected.code
        assert res['locations'][0]['resolution'] == expected_res
        assert res['locations'][0]['name'] == "Wellington"
        assert res['locations'][0]['key'] == "WLG"

    def test_get_hazard_for_gridded_with_arbitrary_locations(self, mock_query_response, monkeypatch, graphql_client):

        mocked_qry = mock.Mock(return_value=mock_query_response)
        monkeypatch.setattr(nshm_hazard_graphql_api.schema.toshi_hazard.datasets, 'get_hazard_curves', mocked_qry)

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
            "GRIDDED_THE_THIRD",
        )

        executed = graphql_client.execute(QUERY)
        print(executed)
        res = executed['data']['hazard_curves']

        assert res['ok'] is True
        assert mocked_qry.call_count == 1

        mocked_qry.assert_called_with(
            ['-37.000~174.800'],
            [400, 250],
            'GRIDDED_THE_THIRD',
            ['PGA', 'SA(0.5)'],
            aggs=["mean", "0.005", "0.995", "0.1", "0.9"],
            strategy='d2',
        )
