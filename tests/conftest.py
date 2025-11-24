import itertools
import os
import pytest
from graphene.test import Client

from nzshm_common.location import CodedLocation
from nzshm_common.location.location import LOCATIONS_BY_ID
from nshm_hazard_graphql_api.schema import schema_root
from dotenv import find_dotenv, load_dotenv
from toshi_hazard_store.query.datasets import AggregatedHazard


@pytest.fixture(scope='session', autouse=True)
def load_env():
    env_file = find_dotenv('.env.tests')
    load_dotenv(env_file)


@pytest.fixture(scope="module")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.unsetenv("AWS_PROFILE")
    os.unsetenv("PROFILE")
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


# @pytest.fixture(scope="module")
# def s3(aws_credentials):
#     with mock_s3():
#         yield boto3.client("s3", region_name="us-east-1")

# @pytest.fixture(scope="module")
# def cloudwatch(aws_credentials):
#     with mock_mock_cloudwatch():
#         yield boto3.client("cloudwatch", region_name="us-east-1")


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


# def build_hazard_aggregation_models():
#     # n_lvls = 29
#     # lvps = list(map(lambda x: model.LevelValuePairAttribute(lvl=x / 1e3, val=(x / 1e6)), range(1, n_lvls)))
#     # for loc, vs30, agg in itertools.product(locs[:5], vs30s, aggs):
#     #     for imt, val in enumerate(imts):
#     #         yield model.HazardAggregation(
#     #             values=lvps,
#     #             vs30=vs30,
#     #             agg=agg,
#     #             imt=val,
#     #             hazard_model_id=HAZARD_MODEL_ID,
#     #         ).set_location(loc)


@pytest.fixture(scope="module")
def many_rlz_args():
    yield dict(
        TOSHI_ID='FAk3T0sHi1D==',
        vs30s=[250, 350, 450],
        imts=['PGA', 'SA(0.5)'],
        locs=[
            CodedLocation(wlg['latitude'], wlg['longitude'], 0.001),
            CodedLocation(dud['latitude'], dud['longitude'], 0.001),
        ],
        rlzs=[x for x in range(5)],
    )


@pytest.fixture(scope='module')
def mock_query_response(many_rlz_args, *args, **kwargs):

    def generator_fn():
        for loc, vs30, imt, agg in itertools.product(
            many_rlz_args["locs"][:5], many_rlz_args["vs30s"], many_rlz_args["imts"], ['mean', 'cov', '0.95']
        ):
            yield AggregatedHazard(
                compatable_calc_id="NZSHM22",
                hazard_model_id=HAZARD_MODEL_ID,
                nloc_001=loc.resample(0.001).code,
                nloc_0=loc.resample(1).code,
                imt=imt,
                vs30=vs30,
                agg=agg,
                values=[(x / 1000) for x in range(44)],
            ).to_imt_values()

    yield generator_fn()


@pytest.fixture(scope='module')
def graphql_client():
    yield Client(schema_root)


@pytest.fixture(scope='module')
def locations():
    yield locs
