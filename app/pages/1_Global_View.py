import streamlit as st

import sys
sys.path.insert(0,'..')

import global_analysis as ga
from utils import GraphConnector


###############
# PAGE CONFIG #
###############

st.set_page_config(
    page_title="Global View",
    page_icon="🌆",
    layout="wide"
)

###########
# SIDEBAR #
###########

st.sidebar.header("Global View")
st.sidebar.markdown(
    """Navigation  
    - [Opportunities Summary](#opportunities-summary)  
    - [Geographic Distribution](#geographic-distribution-of-opportunity-value)  
    - [Subscription Analysis](#subscription-analysis)  
    """
)
st.sidebar.markdown("---")

# Init connection to neo4j
conn = GraphConnector()

def total_col(df, col):
    return df[col].sum()

def rename_col(df, oldcol, newcol):
    df.rename(columns={oldcol:newcol}, inplace=True)


# Opportunities
# All opps data
all_opps_df = ga.get_number_opportunities_per_account(conn)
rename_col(all_opps_df, 'COUNT(opp)', 'Opportunities')
all_opps = total_col(all_opps_df, 'Opportunities')
all_opps_dist = ga.create_distribution_chart(
    all_opps_df,
    'Opportunities'
)

# Open opps data
open_opps_df = ga.get_number_open_opps_per_account(conn)
rename_col(open_opps_df, 'COUNT(opp)', 'Opportunities')
open_opps = total_col(open_opps_df, 'Opportunities')
open_opps_dist = ga.create_distribution_chart(
    open_opps_df,
    'Opportunities'
)

# Closed opps data
closed_opps_df = ga.get_number_closed_won_opps_per_account(conn)
rename_col(closed_opps_df, 'COUNT(opp)', 'Opportunities')
closed_opps = total_col(closed_opps_df, 'Opportunities')
closed_opps_dist = ga.create_distribution_chart(
    closed_opps_df,
    'Opportunities'
)

# Opp streamlit
st.markdown("# Opportunities Summary")
st.markdown("## All Opportunities")
st.metric(
    label='All Opportunities',
    value=all_opps
)
st.plotly_chart(all_opps_dist)

st.markdown("## Open Opportunities")
st.metric(
    label='Open Opportunities',
    value=open_opps
)
st.plotly_chart(open_opps_dist)

st.markdown('## Won Opportunities')
st.metric(
    label='Won Opportunities',
    value=closed_opps
)
st.plotly_chart(closed_opps_dist)
st.markdown("---")

# Pick a chart (maybe not useful)
#st.markdown('# Feature Distributions')
#node_or_edge = st.radio(
#    "Which category do you want to see a summary for?",
#    ("Nodes", "Edges")
#)
#
#if node_or_edge == "Nodes":
#    node_labels = ga.get_node_labels(conn)
#    label = st.selectbox(
#        "Select a Label:",
#        node_labels
#    )
#    node_props = ga.get_node_properties(conn, label)
#    prop = st.selectbox(
#        "Select a Property:",
#        node_props
#    )
#    dist = ga.get_distribution_adj_per_account(
#        conn,
#        adj_label=label,
#        adj_prop=prop
#    )
#    dist_fig = ga.create_distribution_chart(dist, 'COUNT(acct.accountId)')
#    st.plotly_chart(dist_fig)
#elif node_or_edge == "Edges":
#    edge_labels = ga.get_edge_types(conn)
#    label = st.selectbox(
#        "Select a Label:",
#        edge_labels
#    )

# Map viz
st.markdown("# Geographic Distribution of Opportunity Value")
open_value_per_state = ga.get_opp_value_per_state(conn)
rename_col(
    open_value_per_state,
    'SUM(toInteger(opp.amount))',
    'value'
)
rename_col(
    open_value_per_state,
    'st.state',
    'State'
)
map_fig = ga.create_map_distribution_chart(open_value_per_state)
st.pydeck_chart(map_fig)


# Subscription Analysis
st.markdown('# Subscription Analysis')
sub_data = ga.sub_data_pipeline()

st.markdown("## New Subscribers per Day")
sma_periods = st.selectbox(
    "Number of Days for Trendline",
    [i for i in range(30)],
    index=10
)
ts_fig, sub_dist_fig = ga.create_ts_dist_charts(sub_data, sma_periods)
st.plotly_chart(ts_fig)

st.markdown("## Distribution of Days by New Subscriber Count")
st.plotly_chart(sub_dist_fig)

st.markdown("## Correlation Analysis")
st.write("This information is best viewed by zooming in. The labels will follow.")
corr_fig = ga.correlation_heatmap(sub_data)
st.plotly_chart(corr_fig, use_container_width=True)

st.markdown("## Subscription Prediction")
st.write(
    """Provide the data below for a client to get an approximate likielihood
    that they will become a subscriber within 6 weeks of having first
    signed up for our service. Values can be typed into each field.
    """
)

with st.container():
    st.write("Number of tests passed per week")
    cs = st.columns(6)
    passes = {}
    for i, ci in enumerate(cs, 1):
        with ci:
            n_pass = st.number_input(
                f'Passes in Week {i}',
                value=0
            )
            passes.update({f'num_passes_week_{i}': n_pass})

with st.container():
    st.write("Number of tests failed per week")
    cs = st.columns(6)
    failed = {}
    for i, ci in enumerate(cs, 1):
        with ci:
            n_fail = st.number_input(
                f'Failures in Week {i}',
                value=0
            )
            failed.update({f'num_failures_week_{i}': n_fail})

with st.container():
    st.write("Total duration of all tests per week")
    cs = st.columns(6)
    duration = {}
    for i, ci in enumerate(cs, 1):
        with ci:
            dur = st.number_input(f'Duration in Week {i}')
            duration.update({f'sum_test_duration_{i}': dur})

with st.container():
    st.write("Number of new members added per week")
    cs = st.columns(6)
    members = {}
    for i, ci in enumerate(cs, 1):
        with ci:
            mems = st.number_input(
                f'New members in Week {i}',
                value=0
            )
            members.update({f'num_new_members_added_week_{i}': mems})

calculate = st.button('Predict')
if calculate:
    feature_vector = ga.build_feature_vector(
        passes_feats=passes,
        failed_feats=failed,
        duration_feats=duration,
        members_feats=members
    )
    model = ga.get_sub_model()
    pred = ga.make_prediction(model, feature_vector)
    msg = "### The approximate likelihood the user will subscribe is: {:.2f}%"\
            .format(pred*100)
    st.markdown(msg)
    calculate = False
