import re
import joblib

import pandas as pd
import plotly.express as px
import pydeck as pdk

from sklearn.preprocessing import StandardScaler

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


################
# SUBSCRIPTION #
################

def load_sub_data(
    path: str="https://maca-screener.s3.us-east-2.amazonaws.com/churn-dataset.csv"
):
    return pd.read_csv(path)


def preprocess_sub_data(data: pd.DataFrame):
    # Format date columns
    date_cols = [
        'organization_created_at',
        'first_run_at',
        'first_used_feature_a',
        'first_used_feature_b',
        'subscription_created_at'
    ]
    for col in date_cols:
        data[col] = pd.to_datetime(data[col]).dt.date

    # Remove invalid and unwanted data
    data = data[
        ~(data['subscription_created_at']<data['organization_created_at'])
    ].reset_index(drop=True)

    data = data.drop(
        columns=[c for c in data.columns if ('7' in c) or ('8' in c)]
    )

    data = data[
        ~((data['subscription_created_at']-data['organization_created_at'])\
            .dt.days >= 42) |
        (data['subscription_created_at'].isna())
    ]

    # Create binary value for subscription status
    data['sub_in_6_weeks'] = (
        (
            data['first_run_at']-data['subscription_created_at']
        ).fillna(pd.Timedelta(1e5, unit='D')).dt.days.astype(int) < 42
    )*1
    data['id'] = data.index
    return data


def sub_feature_engineering(data: pd.DataFrame):
    date_cols = [
        'organization_created_at',
        'first_run_at',
        'first_used_feature_a',
        'first_used_feature_b',
    ]
    for i, col in enumerate(date_cols[:-1], start=1):
        if i >= 2:
            data[f"{col}_minus_{date_cols[0]}"] = (data[col] - data[date_cols[0]]).dt.days
        if i >= 3:
            data[f"{col}_minus_{date_cols[1]}"] = (data[col] - data[date_cols[1]]).dt.days
        if i >= 4:
            data[f"{col}_minus_{date_cols[2]}"] = (data[col] - data[date_cols[2]]).dt.days
    data.fillna(0, inplace=True)
    return data


def sub_data_pipeline():
    data = load_sub_data()
    data = preprocess_sub_data(data)
    data = sub_feature_engineering(data)
    return data


##############
# PREDICTION #
##############

def get_sub_model(path:str='./models/weights/sub/model.joblib'):
    model = joblib.load(path)
    return model


def build_feature_vector(passes_feats: dict,
                         failed_feats: dict,
                         duration_feats: dict,
                         members_feats: dict
                        ):
    data = passes_feats | failed_feats | duration_feats |members_feats
    # These had minimal impact of the ultimate prediction of the model
    other_vars = {
        'first_run_at_minus_organization_created_at': 0,
        'first_used_feature_a_minus_organization_created_at': 0,
        'first_used_feature_a_minus_first_run_at': 0,
        'first_used_feature_b_minus_organization_created_at': 0,
        'first_used_feature_b_minus_first_run_at': 0,
        'first_used_feature_b_minus_first_used_feature_b': 0
    }
    data = data | other_vars
    feature_vector = pd.DataFrame.from_dict(data, orient='index').transpose()
    return feature_vector.astype(float).values


def make_prediction(model, feature_vector):
    return model.predict_proba(feature_vector)[0][1]


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


def create_ts_dist_charts(data: pd.DataFrame, sma_periods=3):
    data = data[
        ['subscription_created_at','sub_in_6_weeks']
    ][data['subscription_created_at']!=0].groupby(
        'subscription_created_at'
    ).sum()
    sub_date_min = data.index.min()
    sub_date_max = data.index.max()
    idx = pd.period_range(
        start=sub_date_min,
        end=sub_date_max,
        freq='D'
    )
    data.reindex(idx, fill_value=0)
    data[f'{sma_periods} Day Moving Average'] = data[
        'sub_in_6_weeks'
    ].rolling(sma_periods).mean()
    data.columns = [c.replace("_"," ").title() for c in data.columns]
    data.index.name = 'Subscription Creation Date'
    ts_fig = px.line(data)

    dist_fig = px.histogram(
        data,
        x='Sub In 6 Weeks',
        marginal='violin',
        hover_data=['Sub In 6 Weeks']
    )
    return ts_fig, dist_fig


def correlation_heatmap(data: pd.DataFrame):
    cols = [c.replace("_"," ").title() for c in data.columns]
    data.columns = cols
    data.drop(columns=['Organization Id','Id'], inplace=True)
    data.drop(columns=[c for c in data.columns if 'Minus' in c], inplace=True)
    corr = data.corr()
    corr_fig = px.imshow(corr)
    return corr_fig
