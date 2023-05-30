import streamlit as st
import streamlit.components.v1 as components

import sys
sys.path.insert(0, '..')

import account_analysis as aa
from utils import GraphConnector

# Settings and basic content
st.set_page_config(
    page_title="Account View",
    layout='wide',
    page_icon="🏡"
)
st.sidebar.header("Account View")
conn = GraphConnector()
acct_num = st.sidebar.selectbox(
    'Select an account:',
    aa.get_account_numbers(conn)
)
conn.close()

st.sidebar.markdown(
    """Navigation  
    - [Summary Statistics](#summary-statistics)  
    - [Account Graph](#account-graph)  
    - [Opportunities](#opportunities)  
    - [Advanced Analytics](#advanced-analytics)
    """
)
st.sidebar.markdown("---")

if acct_num:
    try:
        conn = GraphConnector()
        subgraph = aa.get_account_subgraph(acct_num, conn)
        company_name = aa.get_node_company_name(acct_num, conn)
        opportunities = aa.get_account_opportunities(acct_num, conn)
        opportunities = aa.preproc_results_dataframe(opportunities)
        metrics, dfs = aa.opportunity_summary(opportunities)
        if len(opportunities) == 1:
            dist_fig = pie_fig= None
        else:
            dist_fig, pie_fig = aa.opportunity_summary_graphs(dfs)
    except Exception as err:
        st.markdown(f"Oh no! There is an error with account {acct_num}!")
        # If time, write the error to a log file
        # st.write(err)
        st.stop()
        conn.close()

    # Account summary
    st.markdown(f'# Account {acct_num} : {company_name}')
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

        st.markdown('### Distribution of Open Opportunity Stages')
        if pie_fig is not None:
            st.plotly_chart(pie_fig)
        else:
            st.write('There is only 1 opportunity, cannot generate figure.')

    # Visualize account subgraph
    st.markdown('---\n## Account Graph')
    physics = not st.checkbox(
        'Disable Graph Physics'
    )
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

    st.markdown("### 10-K Financial Sentiment Analysis")
    if acct_num < 7:
        sents = aa.get_financial_sentiments(acct_num)
        stats = aa.get_dist_stats_sentiment(sents)
        sent_dist_fig = aa.create_sentiment_dist(sents)

        st.markdown(
            """#### Distribution of Item 7 sentence sentiments for most recent 10-K"""
        )
        st.write(
            """Values closer to 1 indicate a more positive sentiment. Values
            closer to -1 indicate a more negative sentiment.
            """
        )
        st.plotly_chart(sent_dist_fig)
        with st.container():
            c1,c2,c3,_,c4 = st.columns(5)
            with c1:
                st.metric(
                    label="Lower 95%-CI",
                    value=stats['2.5%'].round(4)
                )
            with c2:
                st.metric(
                    label="Mean Sentiment",
                    value=stats['mean'].round(4)
                )
            with c3:
                st.metric(
                    label="Upper 95%-CI",
                    value=stats['97.5%'].round(4)
                )
            with c4:
                st.metric(
                    label="Standard Deviation",
                    value=stats['std'].round(4)
                )
        with st.container():
            cs = st.columns(5)
            pctl = ['min','25%','median','75%','max']

            for p,c in zip(pctl, cs):
                with c:
                    st.metric(
                        label=p.title(),
                        value=stats[p].round(4)
                    )
        low_ci_interp = aa.interpret_value(
            stats['mean']-stats['std']*1.96
        )
        mean_interp = aa.interpret_value(stats['mean'])
        high_ci_interp = aa.interpret_value(
            stats['mean']+stats['std']*1.96)

        msg = (
            f'''Based on the Item 7 (Executive Summary) for the most recent 10-K
            filing, the following interpretations may be taken away:  
             - From a worst of "{low_ci_interp}"  
             - To a best of "{high_ci_interp}"  
             - With a most probable being "{mean_interp}"'''
        )
        st.markdown(msg)
        st.write(
            """NOTE: These are possibilities based on a AI model's training on
            historical 10-Ks and are merely to give a rough range of
            possibilities that take recent fiscal events into account."""
        )

    conn.close()
