"""tests to show that the dataset query drop-in replacement for the dynamodb query works OK"""

import pytest
import pathlib
import json
from nzshm_common.location import CodedLocation
import nshm_hazard_graphql_api.schema.toshi_hazard.hazard_curves
import nshm_hazard_graphql_api.schema.toshi_hazard.datasets


fixture_path = pathlib.Path(__file__).parent / 'fixtures'


@pytest.fixture(autouse=True)
def set_expected_vs30(monkeypatch):
    monkeypatch.setattr(nshm_hazard_graphql_api.schema.toshi_hazard.hazard_curves, "DATASET_VS30", [400, 750])


@pytest.fixture()
def hazagg_fixture_fn():
    def fn(model, imt, loc, agg, vs30):
        """Test helper function"""
        fxt = fixture_path / 'HAZAGG_2022_API_JSON' / f"{model}_{imt}_{loc}_{agg}_{vs30}.json"
        assert fxt.exists
        return json.load(open(fxt))

    yield fn


@pytest.fixture()
def dataset_locations():
    yield [
        CodedLocation(-36.87, 174.77, 0.001),
        CodedLocation(-41.3, 174.78, 0.001),
    ]


@pytest.mark.parametrize("vs30", [400, 750])
@pytest.mark.parametrize("imt", ["PGA", "SA(0.5)"])
@pytest.mark.parametrize("aggr", ["mean"])
def test_hazard_curve_query_using_dataset(graphql_client, monkeypatch, hazagg_fixture_fn, vs30, imt, aggr):
    dspath = fixture_path / 'AGG_THS1.1_DFG'
    assert dspath.exists()

    monkeypatch.setattr(nshm_hazard_graphql_api.schema.toshi_hazard.datasets, 'DATASET_AGGR_URI', str(dspath))
    monkeypatch.setattr(nshm_hazard_graphql_api.schema.toshi_hazard.hazard_curves, 'DATASET_AGGR_ENABLED', True)

    model = "NSHM_v1.0.4"
    locn = "-41.300~174.780"

    expected = hazagg_fixture_fn(model, imt, locn, aggr, vs30)

    QUERY = f"""
        query {{
            hazard_curves (
                hazard_model: "{model}"
                imts: ["{imt}"]
                locs: ["{locn}"]
                aggs: ["{aggr}"]
                vs30s: [{vs30}]
                resolution: 0.01
                )
            {{
                ok
                curves {{
                    hazard_model
                    imt
                    loc
                    agg
                    vs30
                    curve {{
                        levels
                        values
                    }}
                }}
                locations {{
                  lat
                  lon
                  resolution
                  code
                  name
                  key
                }}
            }}
        }}
    """

    print(QUERY)

    executed = graphql_client.execute(QUERY)

    print(executed)
    res = executed['data']['hazard_curves']

    print(res)
    assert res['ok'] is True
    assert res['curves'][0]['hazard_model'] == expected['data']['hazard_curves']['curves'][0]['hazard_model']
    assert res['curves'][0]['imt'] == expected['data']['hazard_curves']['curves'][0]['imt']
    assert res['curves'][0]['vs30'] == expected['data']['hazard_curves']['curves'][0]['vs30']
    assert res['curves'][0]['agg'] == expected['data']['hazard_curves']['curves'][0]['agg']
    assert res['curves'][0]['loc'] == expected['data']['hazard_curves']['curves'][0]['loc']

    assert res['curves'][0]['curve']['levels'] == expected['data']['hazard_curves']['curves'][0]['curve']['levels']

    # Check values from original DynamoDB table vs new aggregate pyarrow dataset.
    # note the value differences here (< 5e-9) are down to minor changes in THP processing.
    for idx, level in enumerate(res['curves'][0]['curve']['levels']):
        res_value = res['curves'][0]['curve']['values'][idx]
        exp_value = expected['data']['hazard_curves']['curves'][0]['curve']['values'][idx]
        print(
            f"testing idx: {idx} level: {level} res_value: {res_value}"
            f" expected_value: {exp_value}. diff: {exp_value-res_value}"
        )
        assert res_value == pytest.approx(exp_value, abs=3e-8)
