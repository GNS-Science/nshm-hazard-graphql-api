"""
Console script for testing performance options


 - we currently have DATASET data available for vs302 = [400, 1500]
 - any queries to other vs#) fill force use of legacy dyanamoDB queries

"""

import logging
import click
import json
import os
import itertools
import datetime as dt

import gql
from gql.transport.requests import RequestsHTTPTransport

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.WARNING)

def get_client(url, headers, retries=0, timeout=1.0):
    transport = RequestsHTTPTransport(url=url, headers=headers, use_json=True, retries=retries, timeout=timeout)
    return gql.Client(transport=transport, fetch_schema_from_transport=False)

def run_query(client, variable_values):

    query = """
    query($imts: [String], $vs30s: [Int], $locs: [String], $aggs: [String], $strategy: String ) { 
        hazard_curves(
            hazard_model: "NSHM_v1.0.4"
            imts: $imts
            vs30s: $vs30s
            locs: $locs
            aggs: $aggs
            query_strategy: $strategy
        ) {
            curves {
                hazard_model
                imt
                curve {
                    levels
                    values
                }
            }
        }
    }
    """

    logger.debug('query: %s', query)
    logger.debug('variable_values: %s', variable_values)

    gql_query = gql.gql(query)
    # TODO: started asserting after update to v3.0+ gql
    # if self._with_schema_validation:
    #     self._client.validate(gql_query)  # might throw graphql.error.base.GraphQLError

    response = client.execute(gql_query, variable_values)
    if response.get('errors') is None:
        return response
    else:
        logger.warning(response)
        return None




@click.command()
# @click.argument('source')
# @click.argument('target')
# @click.option("-p", "--parts", help="comma-separated list of partition keys for the target DS", default="vs30,nloc_0")
@click.option('-v', '--verbose', is_flag=True, default=False)
def run_test(
    # source,
    # target,
    # parts,
    verbose,
):
    """Compact and repartition the dataset.

    Can be used on both realisation and aggregate datasets.

    Arguments:\n

    SOURCE: path to the source (folder OR S3 URI).\n
    TARGET: path to the target (folder OR S3 URI).
    """

    if verbose:
        pass

    vars = {"imts": ["PGA"], "vs30s": [1500], "locs": ["-41.300~174.800"],  "aggs": ["mean"], #, "0.995", "0.005"],
            "strategy": "dyn"}
               
    dynamo_wlg = {
        "hazard_model":"NSHM_v1.0.4",
               "vs30s":[400],
               "imts":["PGA","SA(0.1)","SA(0.2)","SA(0.3)","SA(0.4)","SA(0.5)","SA(0.7)","SA(1.0)","SA(1.5)","SA(2.0)","SA(3.0)","SA(4.0)","SA(5.0)","SA(6.0)","SA(7.5)","SA(10.0)"],
               "locs":["-41.3~174.78"],
               "aggs":["mean","0.05","0.95","0.1","0.9"],
               "resolution":0.2,
               "strategy": "dyn"
               }

    URL = "https://ggflyl8t3g.execute-api.ap-southeast-2.amazonaws.com/dev/graphql"
    # URL = "http://localhost:5000/graphql"
    API_TOKEN = os.getenv("API_TOKEN", "")
    headers = { "x-api-key": API_TOKEN }

    # print(headers)
    client = get_client(url=URL, headers=headers, timeout=25)
    # print(client)


    locs = ["WLG", "-41.300~174.800", "-37.100~175.100"] 
    vs30s = [400, 1500] # 500,1000,
    strategies = ['dyn', 'd1', 'd2'] #, 'd0']'dyn', 
   
    vars = dynamo_wlg
    click.echo('curves\tvs30\tlocation\ttype\tduration (s)\tresult')

    for loc, vs30, strategy in itertools.product(locs, vs30s, strategies):

        vars = dynamo_wlg.copy()

        vars['vs30s'] = [vs30]
        vars['locs'] = [loc]
        vars['strategy'] = strategy

        try:
            t0 = dt.datetime.now()            
            result = run_query(client, variable_values=vars)
            elapsed = dt.datetime.now() - t0
            click.echo(f"{len(result['hazard_curves']['curves'])}\t{vs30}\t{loc}\t{strategy}\t{elapsed.total_seconds()}\tOK")
        except Exception:
            elapsed = dt.datetime.now() - t0
            click.echo(f"0\t{vs30}\t{loc}\t{strategy}\t{elapsed.total_seconds()}\tFAIL")


if __name__ == "__main__":
    run_test()