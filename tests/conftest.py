# import boto3
import itertools
import os
import pytest
from graphene.test import Client

# from moto import mock_s3  # , mock_cloudwatch
from toshi_hazard_store import model
from nzshm_common.location import CodedLocation
from nzshm_common.location.location import LOCATIONS_BY_ID
from nshm_hazard_graphql_api.schema import schema_root
from dotenv import find_dotenv, load_dotenv


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


def build_hazard_aggregation_models():
    n_lvls = 29
    lvps = list(map(lambda x: model.LevelValuePairAttribute(lvl=x / 1e3, val=(x / 1e6)), range(1, n_lvls)))
    for loc, vs30, agg in itertools.product(locs[:5], vs30s, aggs):
        for imt, val in enumerate(imts):
            yield model.HazardAggregation(
                values=lvps,
                vs30=vs30,
                agg=agg,
                imt=val,
                hazard_model_id=HAZARD_MODEL_ID,
            ).set_location(loc)


@pytest.fixture(scope='module')
def mock_query_response(*args, **kwargs):
    return build_hazard_aggregation_models()


@pytest.fixture(scope='module')
def graphql_client():
    yield Client(schema_root)


@pytest.fixture(scope='module')
def locations():
    yield locs
