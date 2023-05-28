import streamlit as st
import streamlit.components.v1 as components

import sys
sys.path.insert(0, '..')

import account_analysis as aa

# Settings and basic content
st.set_page_config(
    page_title="Account View",
    layout='wide',
    page_icon="🏡"
)
st.sidebar.header("Account View")
st.sidebar.markdown(
    """Navigation  
    - [Summary Statistics](#summary-statistics)  
    - [Account Graph](#account-graph)  
    - [Opportunities](#opportunities)  
    - [Advanced Analytics](#advanced-analytics)
    """
)
st.sidebar.markdown("---")

acct_num = st.sidebar.selectbox(
    'Select an account:',
    aa.get_account_numbers()
)

st.sidebar.header('Graph Behavior')
physics = not st.sidebar.checkbox(
    'Disable Graph Physics'
)

if acct_num:
    subgraph = aa.get_account_subgraph(acct_num)
    opportunities = aa.get_account_opportunities(acct_num)
    opportunities = aa.preproc_results_dataframe(opportunities)
    metrics, dfs = aa.opportunity_summary(opportunities)
    if len(opportunities) == 1:
        dist_fig = pie_fig= None
    else:
        dist_fig, pie_fig = aa.opportunity_summary_graphs(dfs)

    # Account summary
    st.markdown(f'# Company {acct_num}')
    st.markdown("---\n## Summary Statistics")
    st.write("Percentages are for each row.")
    with st.container():
        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                label='Total Account Value',
                value='${:,.2f}'.format(metrics['Total Account Value'])
            )
        with col2:
            st.metric(
                label='Open Opp Value',
                value='${:,.2f}'.format(metrics['Total Open Opp Value']),
                delta='{:,.1f}%'.format(metrics['% Total Value Open']*(-100)),
                delta_color='off'
            )
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label='Closed Won Opp Value',
                value='${:,.2f}'.format(metrics['Total Closed Won Opp Value']),
                delta='{:,.1f}%'.format(metrics['% Closed Value Won']*100),
                delta_color='off'
            )
        with col2:
            st.metric(
                label='Closed Lost Opp Value',
                value='${:,.2f}'.format(metrics['Total Closed Lost Opp Value']),
                delta='{:,.1f}%'.format(
                    (1 - metrics['% Closed Value Won'])*(-100)
                ),
                delta_color='off'
            )

    with st.container():
        st.markdown('### Distribution of Opportunity Values')
        if dist_fig is not None:
            st.plotly_chart(dist_fig)
        else:
            st.write('There is only 1 opportunity, cannot generate figure.')

        st.markdown('### Distribution of Opportunity Stages')
        if pie_fig is not None:
            st.plotly_chart(pie_fig)
        else:
            st.write('There is only 1 opportunity, cannot generate figure.')

    # Visualize account subgraph
    st.markdown('---\n## Account Graph')
    st.write(
        """The unlabeled central node is the company on the account and the
        other unlabeled node connected to it is the year it was founded. I am
        uncertain why the labels are not displaying, but this is not the most
        pressing issue for this screener 🙂.""")
    viz = aa.visualize_graph(subgraph)
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
    st.markdown("---\n## Opportunities")
    st.dataframe(opportunities)

    # Advanced analytics
    st.markdown("---\n## Advanced Analytics")

    st.markdown("### Financial Sentiment")

    st.markdown("### Opportunity Pricing")

    st.markdown("### Opportunity Success Likelihood")
