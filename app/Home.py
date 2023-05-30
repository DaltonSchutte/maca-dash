import streamlit as st

st.set_page_config(
    page_title="SalesForce Explorer",
    page_icon="💸"
)

st.write("# Analytics Dashboard")

st.sidebar.success("Select a View")

st.markdown(
    """
    Welcome to the SalesForce Analytics Dashboard!

    There are two views to choose:
    - Global View
    - Account View

    Each will provide you with a different level of granularity regarding the
    operations of your sales team to help you better understand where your
    strengths and weaknesses may lie.

    ## Global View
    ### Opportunities Summary
    This gives a high-level overview of all of the opportunities relevant to
    the your team's bottom line. It also breaks out to show what the
    distribution of open and won opportunities per account look like to give a
    rough idea of where the overall performance is at.

    ### Geographic Distribution
    Here, an interactive map shows a heatmap distribution of where the open
    opportunity value lies. Darker red indicates a higher density of potential
    revenue. This can help determine if there is sufficient presence throughout
    the areas you do business. This could inform which conferences you table at
    or where you hire additional account managers.

    ### Subscription Analysis
    The two charts shown here give the number of new account subscriptions on a
    daily basis and a distribution of the number of new subscriptions per day.
    This can help detect trends early or try to identify patterns you can
    leverage to change your sales plan.

    #### Subscription Prediction
    This uses a trained machine learning model to make a guess at the
    likelihood that a client will become a subscriber for your product. Enter
    as many values as you have data for and it will give a rough percentage
    that the client will subscribe. Not meant to be a hard and fast rule, but
    can help you decide where to allocate efforts based on historical data!

    ## Account View
    ### Summary Information and Visuals
    This allows you to select an account by its Account ID and will
    return a collection of useful information regarding the account. This
    includes summary satistics about the value of the account in the form of
    total potential value (Closed Won and Open opportunities), realized value
    (Closed Won opportunities), and outstanding value (Open opportunities).
    There will be a histogram for the opportunity values for each of the the
    categories above and a pie chart showing the distribution of stages for
    all of the opportunities. These charts are interactive so you can zoom,
    scroll, and hover to get additional information.

    ### Account Graph
    The next thing you will see is a graph with all of the important
    information regarding the account! This includes who the contacts at the
    company are, their reporting structure, when the company was founded, the
    annual revenue, what source the account originated from, the billing and
    shipping addresses, and more.

    ### Opportunities Table
    The next object includes a table view of all of the opportunities
    related to this account for easier perusal. These could be shown in the
    graph, but for a busy account this clutters your visualization!

    ### Advanced Analytics
    The final section has a number of interesting results for you to draw
    insights from. This includes:
    - a **"Financial Sentiment"** that uses data from the company's most recent SEC
    fillings to predict how warm the company might be to spending. Values range
    from-1 to 1 where values close to -1 indicate the company may be less
    likely to spend funds on new projects and values close to 1 indicate they
    may be more likely to spend on new projects! The "Financial Sentiment"
    comes from a Deep Neural Network that analyzes the SEC filings to predict
    how likely they are to spend based on recent earnings.
    """
)
