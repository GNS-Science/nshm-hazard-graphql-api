# import boto3
import os
import pytest

# from moto import mock_s3  # , mock_cloudwatch


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
