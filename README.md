# SalesForce-Dash

The context for this dashboard is that it was created from the perspective of
being asked to create a tool to help a sales team at a SaaS company better
understand their clients and their own internal strengths and areas for growth.
I recommend interacting with the dashboard from that lens. The homepage of the
dashboard contains some additional information that more thoroughly describes
the components and sections you will be interacting with. Similar to an
introductory page someone might see when accessing a tool for the first time.

## Installation
The initial setup can take a while (10-20 minutes) to complete due to the creation of the Neo4j database and installation of many python packages (I would. The data that is used is stored on public S3 buckets, so if you want to take a look at the raw csv files you should be able to download them.

This requires Python 3.10.6>= and Neo4j server 5.8.0-community to be installed.
https://neo4j.com/docs/operations-manual/current/installation/

Once Neo4j is installed, you will want to disable the password requirement:
`sudo vim /etc/neo4h/neo4j.conf`  
and uncomment the line  
`dbms.security.auth_enabled=false`  
start neo4j with:  
`sudo neo4j start`  
and run  
`sudo sh ./setup/setup-neo4j.sh`  
to prepare the database. Then, create a python enviornment, activate it, and install the requirements  
`python3 -m venv env`  
`source env/bin/activate`  
`pip3 install -r requirements.txt`  

Finally, you can run jupyter and look at the notebooks in the `./models/training/` directory or run  
`streamlit run ./app/Home.py`  
to launch the service.  

If you set it up locally, a browser window or tab should just open with the dashboard homepage. If you are running it on a cloud server, you will need to copy the External URL it provides you to a browser window.

## Data
### SalesForce Data
I used a tool called Snowfakery to create the synthetic data that this project is built on. The repo for the data generation can be found at `https://github.com/DaltonSchutte/data-gen`. It isn't necessary to run this unless you are curious exactly how the data was generated. The extent of my involvement was collecting everything into a repo and selecting the template that was used. Everything else is handled by Snowfakery.

### 10-K Filings
The filings were scraped using `sec-edgar-downloader` and Item 7 was parsed to
use for inference. A BERT model that was specially trained on SEC documents was
fine-tuned for the sentiment analysis task. The fine-tuning was done using a
subset of a dataset of 10-K filings from 1993-2020.

### Subscription Data
This dataset was from a previous screening project I completed for a company
that offered a SaaS package. That project contained additional data and user
reviews that I did not feel comfortable including in this project. The mdoeling
and analysis was done specially for this project, though does follow a format I
typically use for straight-forward predictive modeling tasks that don't require
deep learning.

## Use
Once setup finishes, a browser window should open with a dashboard for you to explore! No additional work is necessary. There will be notebooks that walk through the model training process if you are curious about my approach to that.

## Notes
- There are some accounts that will error out when selected in the Account
  View. These are due to my sampling of the Opportunity.csv file from 50,000
  alerts, where every account had at least one opportunity, to 20,000 so the
  `setup-neo4j.sh` script would run in a reasonable amount of time. In a
  production setting, there would of course be code to handle this edge case.
  Likely, an account may not even exist to be queried if there is no
  opportunity associated with it.

- In order to give a little additional realism to the experience, I randomly
  assigned companies from the S&P500 to the first 100 accounts. As such,
  none of the analysis for any of those accounts is reflective of the actual
  conditions for any of those companies.
  
- Financial Sentiment Analyses based on the 10-K filings are only available for the first 6 accounts in the Account View.

- The synthetic data that was used to create the SalesForce dataset is somewhat
  predictable in ways. The structures for the account subgraphs from account to
  account are not particularly varied. There also isn't a good matchup between
  states and countries (i.e. the billing address may be 123 Main Orlando
  Montana Spain 87615). This limited the analysis that could be done that would
  be useful and not just illustriative of making more plotly charts.

![](./assets/maca-graph-model.png)
