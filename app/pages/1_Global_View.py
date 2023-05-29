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
    - [Feature Distributions](#feature-distributions)  
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
st.markdown('# Feature Distributions')
node_or_edge = st.radio(
    "Which category do you want to see a summary for?",
    ("Nodes", "Edges")
)

if node_or_edge == "Nodes":
    node_labels = ga.get_node_labels(conn)
    label = st.selectbox(
        "Select a Label:",
        node_labels
    )
    node_props = ga.get_node_properties(conn, label)
    prop = st.selectbox(
        "Select a Property:",
        node_props
    )
    dist = ga.get_distribution_adj_per_account(
        conn,
        adj_label=label,
        adj_prop=prop
    )
    dist_fig = ga.create_distribution_chart(dist, 'COUNT(acct.accountId)')
    st.plotly_chart(dist_fig)
elif node_or_edge == "Edges":
    edge_labels = ga.get_edge_types(conn)
    label = st.selectbox(
        "Select a Label:",
        edge_labels
    )

# Map viz
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
