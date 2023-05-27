// Clear any existing data
MATCH (n) DETACH DELETE n;

//
// ACCOUNT
//
// Load account info into nodes
LOAD CSV WITH HEADERS FROM "https://maca-screener.s3.us-east-2.amazonaws.com/Account.csv" AS row
MERGE (acct:Account {
    accountId: toInteger(row.id),
    name: row.Name,
    type: row.Type,
    billingStreet: row.BillingStreet,
    billingCity: row.BillingCity,
    billingPostalCode: row.BillingPostalCode,
    phoneNumber: row.Phone,
    website: row.Website,
    description: row.Description
    })
MERGE (st1:State {state: row.BillingState})
MERGE (st2:State {state: row.ShippingState})
MERGE (rt:Rating {rating: row.Rating})
MERGE (yr:Year {year: toInteger(row.YearStarted)})
MERGE (src:Source {source: row.AccountSource})
MERGE (cs:CleanStatus {status: row.CleanStatus})
MERGE (own:Ownership {ownership: row.Ownership})
MERGE (ar:AnnualRevenue {annualRevenue:  
    (CASE
     WHEN toInteger(row.AnnualRevenue)<10000 THEN '<10k'
     WHEN 10000<=toInteger(row.AnnualRevenue)<20000 THEN '10M-20M'
     WHEN 20000<=toInteger(row.AnnualRevenue)<30000 THEN '20M-30M'
     WHEN 30000<=toInteger(row.AnnualRevenue)<40000 THEN '30M-40M'
     WHEN 40000<=toInteger(row.AnnualRevenue)<50000 THEN '40M-50M'
     WHEN 50000<=toInteger(row.AnnualRevenue)<60000 THEN '50M-60M'
     WHEN 60000<=toInteger(row.AnnualRevenue)<70000 THEN '60M-70M'
     WHEN 70000<=toInteger(row.AnnualRevenue)<80000 THEN '70M-80M'
     WHEN 80000<=toInteger(row.AnnualRevenue)<90000 THEN '80M-90M'
     WHEN 90000<=toInteger(row.AnnualRevenue)<100000 THEN '90M-100M'
     ELSE '100M<' END)
})
WITH *
MERGE (acct)-[:BILLING_ADR_IN]->(st1)
MERGE (acct)-[:SHIPPING_ADR_IN]->(st2)
MERGE (acct)-[:GIVEN_RATING]->(rt)
MERGE (acct)-[:FOUNDED]->(yr)
MERGE (acct)-[:SOURCED_FROM]->(src)
MERGE (acct)-[:HAS_CLEAN_STATUS]->(cs)
MERGE (acct)-[:IS_CORP_TYPE]->(own)
MERGE (acct)-[:HAS_ANNUAL_REVENUE]->(ar);

//
// CONTACT
//
// Load contact info into nodes
LOAD CSV WITH HEADERS FROM "https://maca-screener.s3.us-east-2.amazonaws.com/Contact.csv" as row
MERGE (con:Contact {
    name: row.Salutation + ' ' + row.FirstName + ' ' + row.LastName,
    title: row.Title,
    department: row.Department,
    contactId: toInteger(row.id),
    reportsTo: (
        CASE
        WHEN row.ReportsToId IS null THEN 'NA'
        ELSE toInteger(row.ReportsToId) END
        )
    })
WITH *
MATCH (acct:Account {accountId: toInteger(row.AccountId)})
MATCH (src:Source {source: row.LeadSource})
MATCH (st:State {state: row.OtherState})
MERGE (con)-[:WORKS_FOR]->(acct)
MERGE (con)-[:SOURCED_FROM]->(src)
MERGE (con)-[:WORKS_IN]->(st);

// Add contact reporting heirarchy relationships
MATCH (sub:Contact WHERE sub.contactId <> 'NA')
MATCH (mgr:Contact WHERE mgr.contactId = sub.reportsTo)
MERGE (sub)-[:REPORTS_TO]->(mgr)
REMOVE sub.reportsToId
REMOVE mgr.reportsToId;

//
// OPPORTUNITY
//
// Load opportunity info into nodes and create relationships in one transaction   
LOAD CSV WITH HEADERS FROM "https://maca-screener.s3.us-east-2.amazonaws.com/Opportunity-Reduced.csv" as row
MERGE (op:Opportunity {
    name: row.Name,
    description: row.Description,
    amount: row.Amount,
    oppId: toInteger(row.id),
    closedDate: row.CloseDate
})
MERGE (stg:Stage {stage: row.StageName})
MERGE (opt:OpportunityType {type: row.Type})
WITH *
MATCH (acct:Account {accountId: toInteger(row.AccountId)})
MATCH (src:Source {source: row.LeadSource})
MATCH (con:Contact {contactId: toInteger(row.ContactId)})
MERGE (op)-[:WITH]->(acct)
MERGE (op)-[:IN_STAGE]->(stg)
MERGE (op)-[:HAS_TYPE]->(opt)
MERGE (op)-[:SOURCED_FROM]->(src)
MERGE (op)-[:WORKING_WITH]->(con);
