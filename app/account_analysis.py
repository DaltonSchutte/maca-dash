from typing import (Dict, Optional)
import re
import warnings

import pandas as pd
import plotly.express as px

import pyvis

import neo4j

try:
    from utils import GraphConnector
except:
    from .utils import GraphConnector

###########
# GLOBALS #
###########

NODE_TEXT_PROPERTIES = {
    "Account": "name",
    "AnnualRevenue": "annualRevenue",
    "CleanStatus": "status",
    "Contact": "name",
    "Ownership": "ownership",
    "Rating": "rating",
    "Source": "source",
    "Stage": "stage",
    "State": "state",
    "Year": "year"
}


#################
# GET FUNCTIONS #
#################

def get_account_numbers(conn: GraphConnector):
    query = (
        "MATCH (acct:Account) "
        "WITH COLLECT(DISTINCT acct.accountId) AS acctIds "
        "RETURN acctIds"
    )
    result = conn.query(query)
    return result.records[0][0]


def get_account_subgraph(acct_num: int, conn: GraphConnector):
    """
    Retrieves the subgraph for a specified account. Excludes any Opportunity
    nodes as they tend to clutter the visualization.

    Parameters
    ----------
    acct_num : int
        The AccountId for the desired account
    """
    query = (
        "MATCH (acct:Account {accountId : $acct_num})-[r1]-(n) "
        "MATCH (m)-[r2]-(con:Contact)-[]-(acct) "
        "WHERE NOT n:Opportunity AND NOT m:Opportunity "
        "RETURN acct,r1,r2,con,n,m;"
    )
    result = conn.query(
        query,
        acct_num=acct_num,
        result_transformer_=neo4j.Result.graph
    )
    return result


def get_node_company_name(acct_num: int, conn: GraphConnector):
    query = (
        "MATCH (acct:Account {accountId: $acct_num})"
        "RETURN acct.name"
    )
    result = conn.query(
        query,
        acct_num=acct_num
    )
    company_name = result.records[0][0]
    return company_name


def get_account_opportunities(acct_num: int, conn: GraphConnector):
    query = (
        "MATCH (acct:Account {accountId: $acct_num})-[]-(opp:Opportunity) "
        "MATCH (opp)-[]-(con:Contact) "
        "MATCH (opp)-[]-(src:Source) "
        "MATCH (opp)-[]-(stg:Stage) "
        "MATCH (opp)-[]-(opt:OpportunityType) "
        "RETURN opp.name, opp.closedDate, opp.amount, "
        "opp.description, con.name, src.source, "
        "stg.stage, opt.type;"
    )
    result = conn.query(
        query,
        acct_num=acct_num,
        result_transformer_=neo4j.Result.data
    )
    result = pd.DataFrame().from_dict(result)
    return result


#######################
# DATA PROC FUNCTIONS #
#######################

def preproc_results_dataframe(result):
    result.columns = [
        'Opp Name',
        'Closed Date',
        'Amount (USD)',
        'Description',
        'Contact Name',
        'Source',
        'Stage',
        'Opp Type'
    ]
    result['Open Date'] = result['Opp Name'].str.extract(
        r'(\d{4}-\d{2}-\d{2}$)'
    )
    result['Company Name'] = result['Opp Name'].str.extract(
        r'(^\D+)'
    )
    result = result[[
        'Company Name',
        'Opp Type',
        'Amount (USD)',
        'Stage',
        'Open Date',
        'Closed Date',
        'Description',
        'Contact Name',
        'Source'
    ]]
    result.loc[:,'Amount (USD)'] = result['Amount (USD)'].astype(int)

    # Remove date in Closed Date if Stage not Closed *
    idx = (~result['Stage'].str.contains('Closed'))
    result.loc[idx, 'Closed Date'] = ''
    return result


def opportunity_summary(result):
    """
    Calculates summary statistics and produces graphs for the dashboard

    TODO:
        Separate into a stats function and a graph function.

    Parameters
    ----------
    result : pd.DataFrame
        Dataframe containing the opportunity data
    """
    total_opps = result[~result['Stage'].str.contains('Closed Lost')]
    closed_won_opps = result[result['Stage'].str.contains('Closed Won')]
    closed_lost_opps = result[result['Stage'].str.contains('Closed Lost')]
    open_opps = result[~result['Stage'].str.contains('Closed')]
    # Account value metrics
    total_account_value = total_opps['Amount (USD)'].sum()
    closed_won_value = closed_won_opps['Amount (USD)'].sum()
    closed_lost_value = closed_lost_opps['Amount (USD)'].sum()
    open_value = open_opps['Amount (USD)'].astype(int).sum()
    pct_closed = closed_won_value / total_account_value
    pct_closed_won = closed_won_value / (1+closed_won_value + closed_lost_value)
    pct_open = open_value / total_account_value

    metrics = {
        "Total Account Value": total_account_value,
        "Total Closed Won Opp Value": closed_won_value,
        "Total Closed Lost Opp Value": closed_lost_value,
        "Total Open Opp Value": open_value,
        "% Total Value Closed": pct_closed,
        "% Closed Value Won": pct_closed_won,
        "% Total Value Open": pct_open
    }

    dfs = {
        "TotalOpps": total_opps,
        "ClosedWonOpps": closed_won_opps,
        "ClosedLostOpps": closed_lost_opps,
        "OpenOpps": open_opps
    }

    return metrics, dfs


#################
# VIZ FUNCTIONS #
#################

def opportunity_summary_graphs(dfs):
    # Data formatting
    total_opps = dfs['TotalOpps'][['Amount (USD)']]
    closed_won_opps = dfs['ClosedWonOpps'][['Amount (USD)']]
    closed_lost_opps = dfs['ClosedLostOpps'][['Amount (USD)']]
    open_opps = dfs['OpenOpps'][['Amount (USD)']]

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        total_opps.loc[:,'Type'] = "Total Opps"
        closed_won_opps.loc[:,'Type'] = "Closed Won Opps"
        closed_lost_opps.loc[:,'Type'] = "Closed Lost Opps"
        open_opps.loc[:,'Type'] = "Open Opps"

    agg = pd.concat([
        total_opps,
        closed_won_opps,
        closed_lost_opps,
        open_opps
    ])

    # Account value summary stats
    value_dist_fig = px.histogram(
        agg,
        x='Amount (USD)',
        color='Type',
        marginal='violin',
        hover_data=agg.columns,
        nbins=20
    )
    stage_pie_fig = px.pie(
        dfs['OpenOpps'],
        values='Amount (USD)',
        names='Stage'
    )
    return value_dist_fig, stage_pie_fig


def visualize_graph(
    graph,
    node_text_properties: Dict = NODE_TEXT_PROPERTIES
):
    viz = pyvis.network.Network(
        height='750px',
        width='100%',
        directed=True,
        notebook=False
    )

    for node in graph.nodes:
        node_label = list(node.labels)[0]
        node_text = node[node_text_properties[node_label]]
        viz.add_node(
            node.element_id,
            str(node_text),
            group=node_label
        )

    for edge in graph.relationships:
        viz.add_edge(
            edge.nodes[0].element_id,
            edge.nodes[1].element_id,
            title=edge.type
        )

    return viz
