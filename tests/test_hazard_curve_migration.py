"""tests to show that the dataset query drop-in replacement for the dynamodb query works OK"""

import pytest
import pathlib
import json
from nzshm_common.location import CodedLocation
import nshm_hazard_graphql_api.schema.toshi_hazard.hazard_curves
import nshm_hazard_graphql_api.schema.toshi_hazard.datasets
from toshi_hazard_store.query import datasets, hazard_query

fixture_path = pathlib.Path(__file__).parent / 'fixtures'


def hazard_graphql_query(model: str, imt: str, locn: list[str], aggr: str, vs30: int, strategy: str) -> str:
    return f"""
        query {{
            hazard_curves (
                hazard_model: "{model}"
                imts: ["{imt}"]
                locs: {locn}
                aggs: ["{aggr}"]
                vs30s: [{vs30}]
                resolution: 0.01
                query_strategy: "{strategy}"
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


@pytest.fixture(autouse=True)
def set_expected_vs30(monkeypatch):
    monkeypatch.setattr(nshm_hazard_graphql_api.schema.toshi_hazard.hazard_curves, "DATASET_VS30", [400, 1500])


@pytest.fixture(scope='module')
def json_hazard():
    fxt = fixture_path / 'API_HAZAGG_SMALL.json'
    assert fxt.exists
    yield json.load(open(fxt))


@pytest.fixture()
def hazagg_fixture_fn(json_hazard):
    def fn(hazard_model, imt, nloc_001, agg, vs30):
        curves = json_hazard['data']['hazard_curves']['curves']
        """A test helper function"""
        nloc_0 = hazard_query.downsample_code(nloc_001, 0.1)
        for curve in curves:
            if (
                curve['hazard_model'] == hazard_model
                and curve['imt'] == imt
                and curve['agg'] == agg
                and curve['loc'] == nloc_0
                and curve['vs30'] == vs30
            ):
                return datasets.AggregatedHazard(
                    'NZSHM22', hazard_model, nloc_001, nloc_0, imt, vs30, agg, curve['curve']['values']
                ).to_imt_values()
        return None

    yield fn


@pytest.fixture()
def dataset_locations():
    yield [
        CodedLocation(-36.87, 174.77, 0.001),
        CodedLocation(-41.3, 174.78, 0.001),
    ]


@pytest.mark.parametrize("vs30", [400, 1500])
@pytest.mark.parametrize("strategy", ['d0', 'd1', 'd2'])
@pytest.mark.parametrize("imt", ["PGA", "SA(0.5)"])
@pytest.mark.parametrize("aggr", ["mean"])
def test_hazard_curve_query_using_dataset(graphql_client, monkeypatch, hazagg_fixture_fn, vs30, imt, aggr, strategy):
    dspath = fixture_path / 'HAZAGG_SMALL'
    assert dspath.exists()

    # monkeypatch.setattr(nshm_hazard_graphql_api.schema.toshi_hazard.datasets, 'DATASET_AGGR_URI', str(dspath))
    monkeypatch.setattr(datasets, 'DATASET_AGGR_URI', str(dspath))
    monkeypatch.setattr(nshm_hazard_graphql_api.schema.toshi_hazard.hazard_curves, 'DATASET_AGGR_ENABLED', True)

    model = "NSHM_v1.0.4"
    locn = "-41.300~174.800"

    expected = hazagg_fixture_fn(model, imt, locn, aggr, vs30)
    print(expected)

    qry = hazard_graphql_query(model, imt, f'["{locn}"]', aggr, vs30, strategy)

    print(qry)
    executed = graphql_client.execute(qry)
    res = executed['data']['hazard_curves']

    assert res['ok'] is True
    assert res['curves'][0]['hazard_model'] == expected.hazard_model_id
    assert res['curves'][0]['imt'] == expected.imt
    assert res['curves'][0]['vs30'] == expected.vs30
    assert res['curves'][0]['agg'] == expected.agg

    # # Check values from original DynamoDB table vs new aggregate pyarrow dataset.
    for idx, value in enumerate(res['curves'][0]['curve']['values']):

        exp_value = expected.values[idx].val
        # exp_level = expected.values[idx].lvl

        print(f"testing idx: {idx} res_value: {value}" f" expected_value: {exp_value}. diff: {exp_value - value}")
        assert value == pytest.approx(exp_value, abs=7e5 - 8)
        # assert value.lvl == exp_level


@pytest.mark.parametrize("locn", ["-48.000~180.000", "-41.123~177.230"])
@pytest.mark.parametrize("vs30", [400, 1500])
@pytest.mark.parametrize("strategy", ['d2'])
@pytest.mark.parametrize("imt", ["PGA", "SA(0.5)"])
@pytest.mark.parametrize("aggr", ["mean"])
def test_hazard_curve_query_data_missing(
    graphql_client, monkeypatch, hazagg_fixture_fn, locn, vs30, imt, aggr, strategy
):
    dspath = fixture_path / 'HAZAGG_SMALL'
    assert dspath.exists()

    monkeypatch.setattr(datasets, 'DATASET_AGGR_URI', str(dspath))
    monkeypatch.setattr(nshm_hazard_graphql_api.schema.toshi_hazard.hazard_curves, 'DATASET_AGGR_ENABLED', True)

    model = "NSHM_v1.0.4"

    qry = hazard_graphql_query(model, imt, f'["{locn}"]', aggr, vs30, strategy)
    executed = graphql_client.execute(qry)

    data = executed['data']['hazard_curves']
    assert data['ok'] is True
    assert len(data['curves']) == 0


@pytest.mark.parametrize("locn", ["-48.000~180.000"])
@pytest.mark.parametrize("vs30", [400, 1500])
@pytest.mark.parametrize("strategy", ['d2'])
@pytest.mark.parametrize("imt", ["PGA", "SA(0.5)"])
@pytest.mark.parametrize("aggr", ["mean"])
def test_hazard_curve_query_data_missing_for_one_location(
    graphql_client, monkeypatch, hazagg_fixture_fn, locn, vs30, imt, aggr, strategy
):
    dspath = fixture_path / 'HAZAGG_SMALL'
    assert dspath.exists()

    monkeypatch.setattr(datasets, 'DATASET_AGGR_URI', str(dspath))
    monkeypatch.setattr(nshm_hazard_graphql_api.schema.toshi_hazard.hazard_curves, 'DATASET_AGGR_ENABLED', True)

    model = "NSHM_v1.0.4"
    good_locn = "-41.300~174.800"
    locations = f'["{good_locn}", "{locn}"]'

    # expected = hazagg_fixture_fn(model, imt, good_locn, aggr, vs30)
    qry = hazard_graphql_query(model, imt, locations, aggr, vs30, strategy)
    executed = graphql_client.execute(qry)

    data = executed['data']['hazard_curves']

    assert data['ok'] is True
    assert len(data['curves']) == 1  # same as expected good_data
