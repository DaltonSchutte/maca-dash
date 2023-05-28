from typing import (Dict, Optional)
import re

from pandas import DataFrame
import plotly.figure_factory as ff
import plotly.express as px

import streamlit as st
import streamlit.components.v1 as components
import pyvis

import neo4j

try:
    from utils import GraphConnector
except:
    from .utils import GraphConnector

###########
# GLOBALS #
###########

CONN = GraphConnector()
NODE_TEXT_PROPERTIES = {
    "Account": "accountId",
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


#############
# FUNCTIONS #
#############

def get_account_numbers():
    query = (
        "MATCH (acct:Account) "
        "WITH COLLECT(DISTINCT acct.accountId) AS acctIds "
        "RETURN acctIds"
    )
    result = CONN.query(query)
    return result.records[0][0]


def get_node_labels():
    """
    Retrieves the node labels in the graph DB

    RETURNS
    -------
    list[str]
        List of node label strings
    """
    result = CONN.query("CALL db.labels();")
    labels = [l[0] for l in result]
    return labels


def get_edge_types():
    """
    Retrieves the edge types in the graph DB

    RETURNS
    -------
    list[str]
        List of edge type strings
    """
    result = CONN.query("CALL db.relationshipTypes();")
    types = [l[0] for l in result]
    return types


def get_account_subgraph(acct_num: int):
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
    result = CONN.query(
        query,
        acct_num=acct_num,
        result_transformer_=neo4j.Result.graph
    )
    return result


def get_account_opportunities(acct_num: int):
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
    result = CONN.query(
        query,
        acct_num=acct_num,
        result_transformer_=neo4j.Result.data
    )
    result = DataFrame().from_dict(result)
    return result

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
    result['Amount (USD)'] = result['Amount (USD)'].astype(int)

    # Remove date in Closed Date if Stage not Closed *
    idx = (~result['Stage'].str.contains('Closed'))
    result['Closed Date'][idx] = ''
    return result


def opportunity_summary(result):
    closed_opps = result[result['Stage'].str.contains('Closed')]
    open_opps = result[~result['Stage'].str.contains('Closed')]
    # Account value metrics
    total_account_value = result['Amount (USD)'].sum()
    closed_value = closed_opps['Amount (USD)'].sum()
    open_value = open_opps['Amount (USD)'].astype(int).sum()
    pct_closed = closed_value / total_account_value
    pct_open = open_value / total_account_value

    metrics = {
        "Total Account Value": total_account_value,
        "Total Closed Opp Value": closed_value,
        "Total Open Opp Value": open_value,
        "% Total Value Closed": pct_closed,
        "% Total Value Open": pct_open
    }

    # Account value summary stats
    value_dist_fig = ff.create_distplot(
        [result['Amount (USD)'],
         closed_opps['Amount (USD)'],
         open_opps['Amount (USD)']
        ],
        ['All Opps', 'Closed Opps', 'Open Opps'],
        bin_size=[0.25,0.25,0.25]
    )
    stage_pie_fig = px.pie(
        result,
        values='Amount (USD)',
        names='Stage'
    )
    return metrics, value_dist_fig, stage_pie_fig


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
            node_text,
            group=node_label
        )

    for edge in graph.relationships:
        viz.add_edge(
            edge.nodes[0].element_id,
            edge.nodes[1].element_id,
            title=edge.type
        )

    return viz

############
# SETTINGS #
############

st.set_page_config(layout='wide')
st.sidebar.markdown("# Maca Explorer")
st.sidebar.markdown("---")
st.sidebar.header('Graph Management')

acct_num = st.sidebar.selectbox(
    'Select an account:',
    get_account_numbers()
)
physics = st.sidebar.checkbox(
    'Toggle Graph Physics'
)

if acct_num:
    subgraph = get_account_subgraph(acct_num)
    opportunities = get_account_opportunities(acct_num)
    opportunities = preproc_results_dataframe(opportunities)
    metrics, dist_fig, pie_fig = opportunity_summary(opportunities)

    # Account summary
    f'# Company {acct_num}'
    with st.container():
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric(
                label='Total Account Value',
                value='${:,.2f}'.format(metrics['Total Account Value'])
            )
        with col2:
            st.metric(
                label='Closed Opp Value',
                value='${:,.2f}'.format(metrics['Total Closed Opp Value']),
                delta='{:,.1f}%'.format(metrics['% Total Value Closed']*100),
                delta_color='off'
            )
        with col3:
            st.metric(
                label='Open Opp Value',
                value='${:,.2f}'.format(metrics['Total Open Opp Value']),
                delta='{:,.1f}%'.format(metrics['% Total Value Open']*(-100)),
                delta_color='off'
            )

    with st.container():
        '## Distribution of Opportunity Values'
        st.plotly_chart(dist_fig)
        st.plotly_chart(pie_fig)

    # Visualize account subgraph
    viz = visualize_graph(subgraph)
    viz.toggle_physics(physics)
    html = viz.generate_html(
        name=f'account{acct_num}.html',
        local=True,
        notebook=False
    )
    components.html(
        html,
        height=750,
        width=750
    )

    # Opportunities dataframe
    st.markdown("---\nOpportunities")
    st.dataframe(opportunities)

