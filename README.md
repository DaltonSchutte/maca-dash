# Maca-Dash

## Installation
The repo can be cloned and from the project root `docker compose up` can be run which will set up and launch the service.  
The initial setup can take a while (10-20 minutes) to complete due to the creation of the Neo4j database. The data that is used is stored on public S3 buckets, so if you want to take a look at the raw csv files you should be able to download them.

### Data Generation
I used a tool called Snowfakery to create the synthetic data that this project is built on. The repo for the data generation can be found at `https://github.com/DaltonSchutte/data-gen`. It isn't necessary to run this unless you are curious exactly how the data was generated. The extent of my involvement was collecting everything into a repo and selecting the template that was used. Everything else is handled by Snowfakery.

## Use
Once setup finishes, a browser window should open with a dashboard for you to explore! No additional work is necessary. There will be notebooks that walk through the model training process if you are curious about my approach to that.

## Notes


## Decisions and Rationale
### 1) Graph Database
I chose to use Neo4j for a couple reasons. One being that visualizing data in terms of relationships between entities can be powerful and allows an individual to use their natural pattern recognition abilities with their expertise to see trends and relationships that would be considerably more difficult to notice in tabular data. Another being that, from a modeling and analytics perspective, relational data can be incredibly powerful and result in improved performance over models that just ingest rows of data. The main reason, however, is curiosity. I was curious to connect a dashboard to a graph database backend, as I've never done something quite like this before. I am also curious to hear how you as folks with more experience with SalesForce and the problem Maca is trying to solve respond to the analytics contained in the dashboard and, generally, how the idea of using a graph for this problem sits with you.  

Below is the graph data model. Normally, this would be something we would iterate on together with a laundry list of usecases and tests to be sure the model is satisfying all of the requirements. However, given the time constraints, I did a couple short iterations of my own trying to envision what the end user would want to see.

![](./assets/maca-graph-model.png)
