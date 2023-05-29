import re

import pandas as pd
import plotly.express as px
import pydeck as pdk

import neo4j

try:
    from utils import GraphConnector
except:
    from .utils import GraphConnector


#################
# GET FUNCTIONS #
#################

def get_node_labels(conn: GraphConnector):
    """
    Retrieves the node labels in the graph DB

    RETURNS
    -------
    list[str]
        List of node label strings
    """
    result = conn.query(
        "CALL db.labels();",
        result_transformer_=neo4j.Result.to_df
    )
    return result.values.flatten().tolist()


def get_node_properties(conn: GraphConnector, node_label: str):
    """
    Retrieves the list of propreties for the node of the specified label

    Fix query builder!! String sub is vulnerabilit

    Parameters
    ----------
    conn
        connection to neo4j database
    node_label
        label of the node to retrieve properties for
    """
    query = (
        f"MATCH (n:{node_label}) "
        "RETURN KEYS(n);"
    )
    result = conn.query(
        query,
        node_label=node_label,
        result_transformer_=neo4j.Result.to_df
    )
    return [p for p in result.values[0][0]]


def get_edge_types(conn: GraphConnector):
    """
    Retrieves the edge types in the graph DB

    RETURNS
    -------
    list[str]
        List of edge type strings
    """
    result = conn.query(
        "CALL db.relationshipTypes();",
        result_transformer_=neo4j.Result.to_df
    )
    return result.values.flatten().tolist()



def get_company_billing_states(conn: GraphConnector):
    """
    Retrieves the billing states for each account

    Parameters
    ----------
    conn
        connection to the Neo4j database
    """
    query = (
        "MATCH (:Account)-[BILLING_ADR_IN]->(st:State) "
        "RETURN st.state;"
    )
    result = conn.query(
        query,
        result_transformer_=neo4j.Result.data
    )
    result = pd.DataFrame().from_dict(result)
    return result.values.tolist()


def get_company_shipping_states(conn: GraphConnector):
    query = (
        "MATCH (:Account)-[SHIPPING_ADR_IN]->(st:State) "
        "RETURN st.state;"
    )
    result = conn.query(
        query,
        result_transformer_=neo4j.Result.data
    )
    result = pd.DataFrame().from_dict(result)
    return result.values.tolist()


def get_number_opportunities_per_account(conn: GraphConnector):
    query = (
        "MATCH (acct:Account)-[]-(opp:Opportunity) "
        "MATCH (opp)-[]-(stg:Stage) "
        "WHERE stg.stage<>'Closed Lost' "
        "RETURN acct.accountId, COUNT(opp);"
    )
    result = conn.query(
        query,
        result_transformer_=neo4j.Result.to_df
    )
    return result


def get_number_open_opps_per_account(conn: GraphConnector):
    query = (
        "MATCH (acct:Account)-[]-(opp:Opportunity) "
        "MATCH (opp)-[]-(stg:Stage) "
        "WHERE stg.stage<>'Closed Won' AND stg.stage<>'Closed Lost' "
        "RETURN acct.accountId, COUNT(opp);"
    )
    result = conn.query(
        query,
        result_transformer_=neo4j.Result.to_df
    )
    return result


def get_number_closed_won_opps_per_account(conn: GraphConnector):
    query = (
        "MATCH (acct:Account)-[]-(opp:Opportunity) "
        "MATCH (opp)-[]-(stg:Stage) "
        "WHERE stg.stage='Closed Won' "
        "RETURN acct.accountId, COUNT(opp);"
    )
    result = conn.query(
        query,
        result_transformer_=neo4j.Result.to_df
    )
    return result


def get_average_opp_value_per_account(conn: GraphConnector):
    query = (
        "MATCH (acct:Account)-[]-(opp:Opportunity) "
        "RETURN acct.accountId, AVG(toInteger(opp.amount));"
    )
    result = conn.query(
        query,
        result_transformer_=neo4j.Result.to_df
    )
    return result


def get_sum_closed_opps_per_account(conn: GraphConnector):
    query = (
        "MATCH (acct:Account)-[]-(opp:Opportunity) "
        "MATCH (opp)-[:IN_STAGE]-(stg:Stage) "
        "WHERE stg.stage='Closed Won "
        "RETURN acct.accountId, SUM(toInteger(opp.amount));"
    )
    result = conn.query(
        query,
        result_transformer_=neo4j.Result.to_df
    )
    return result


def get_sum_open_opps_per_account(conn: GraphConnector):
    query = (
        "MATCH (acct:Account)-[]-(opp:Opportunity) "
        "MATCH (opp)-[:IN_STAGE]-(stg:Stage) "
        "WHERE stg.stage<>'Closed Won AND stg.stage<>'Closed Lost' "
        "RETURN acct.accountId, SUM(toInteger(opp.amount));"
    )
    result = conn.query(
        query,
        result_transformer_=neo4j.Result.to_df
    )
    return result


def get_adj_per_account(conn: GraphConnector,
                        adj_label: str
                       ):
    query = (
        "MATCH (acct:Account)-[]-(n:$adj_label) "
        "RETURN acct, n;"
    )
    result = conn.query(
        query,
        adj_label=adj_label,
        result_transformer_=neo4j.Result.to_df
    )
    return result

def get_distribution_adj_per_account(conn: GraphConnector,
                                     adj_label: str,
                                     adj_prop: str
                                    ):
    query = (
        f"MATCH (acct:Account)-[r]-(n:{adj_label}) "
        f"RETURN n.{adj_prop}, COUNT(acct.accountId);"
    )
    result = conn.query(
        query,
        adj_label=adj_label,
        adj_prop=adj_prop,
        result_transformer_=neo4j.Result.to_df
    )
    return result


def get_opp_value_per_state(conn: GraphConnector):
    query = (
        "MATCH (opp:Opportunity)-[:WITH]->(:Account)"
        "-[:SHIPPING_ADR_IN]->(st:State) "
        "MATCH (opp)-[]->(stg:Stage) "
        "WHERE stg.stage<>'Closed Won' AND stg.stage<>'Closed Lost' "
        "RETURN st.state, SUM(toInteger(opp.amount));"
    )
    result = conn.query(
        query,
        result_transformer_=neo4j.Result.to_df
    )
    return result


#################
# VIZ FUNCTIONS #
#################

def create_distribution_chart(data: pd.DataFrame,
                              feature: str
                             ):
    dist_fig = px.histogram(
        data,
        x=feature,
        marginal='violin',
        nbins=20
    )
    return dist_fig

def create_map_distribution_chart(data: pd.DataFrame):
    loc_data = pd.read_csv(
        './app/resources/statelatlong.csv',
        header=0,
        usecols=['Latitude','Longitude','City']
    ).rename(columns={
        'City':'State',
        'Latitude':'lat',
        'Longitude':'lng'
    })

    comb_data = pd.merge(data, loc_data, on='State')
    comb_data = comb_data[['lng','lat','value']]

    max_val = comb_data['value'].max()

    layer = pdk.Layer(
        'HeatmapLayer',
        data=comb_data,
        get_position=['lng','lat'],
        auto_highlight=True,
        get_weight='value',
        get_radius='value',
        pickable=True,
        elevation_range=[0,1000000],
        extrude=True,
        coverage=1
    )
    view_state = pdk.ViewState(
        latitude=95.7,
        longitude=37.1,
        zoom=6,
        min_zoom=5,
        max_zoom=15,
        pitch=40.5,
        bearing=-20
    )
    deck = pdk.Deck(
        layers=layer,
        views=view_state,
        map_style="light"
    )
    return deck
