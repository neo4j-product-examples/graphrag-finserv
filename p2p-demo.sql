-- Fraud Detection and Entity Resolution Example
-- Reference Demo: https://github.com/neo4j-product-examples/demo-fraud-detection-with-p2p/blob/main/abridged-demo/fraud-detection-demo-with-p2p.ipynb
-- This demo will show how to replicate entity resolution & feature engineering from above with GDS in Snowflake
-- ================================

-- We have to use the correct database, schema and warehouse, and a role that gives us access to these
USE ROLE gds_role;
USE DATABASE gds_db;
USE SCHEMA data_schema;
USE WAREHOUSE gds_warehouse;

-- Show warehouse and compute pool
-- This requires the ACCOUNTADMIN role
-- DESCRIBE WAREHOUSE gds_warehouse;
DESCRIBE COMPUTE POOL gds_compute_pool;

-- Docker image repo and images
SHOW IMAGE REPOSITORIES;
SELECT SYSTEM$REGISTRY_LIST_IMAGES('/gds_db/data_schema/gds_repository');

-- Create a GDS Session service which hosts GDS and exposes Arrow/Bolt and HTTP for this SCPS
DROP SERVICE gds_session;
CREATE SERVICE gds_session
  IN COMPUTE POOL gds_compute_pool
  FROM SPECIFICATION $$
    spec:
      containers:
      - name: session-aio
        image: /gds_db/data_schema/gds_repository/gds_session_aio:latest
        env:
          SNOWFLAKE_WAREHOUSE: gds_warehouse
          SERVER_PORT: 8080
        readinessProbe:
          port: 8080
          path: /healthCheck
      endpoints:
      - name: http
        port: 8080
        protocol: HTTP
        public: false
      logExporters:
        eventTableConfig:
          logLevel: INFO
      $$
   MIN_INSTANCES=1
   MAX_INSTANCES=1;

-- Inspect the GDS session service
SHOW SERVICES;
DESCRIBE SERVICE gds_session;
SELECT SYSTEM$GET_SERVICE_STATUS('gds_session');
CALL SYSTEM$GET_SERVICE_LOGS('gds_session', 0, 'session-aio', 100);

-- Read GDS version from Session
DROP FUNCTION IF EXISTS gds_version_aio();
CREATE FUNCTION gds_version_aio()
    RETURNS varchar
    SERVICE=gds_session
  ENDPOINT=http
  AS '/gdsVersion';

SELECT gds_version_aio();

-- Create project function
DROP FUNCTION IF EXISTS gds_graph_project(varchar, varchar, varchar);
CREATE FUNCTION gds_graph_project(GraphName varchar, NodeTable varchar, RelationshipTable varchar)
    RETURNS variant
    SERVICE=gds_session
  ENDPOINT=http
  AS '/graphProject';
DESCRIBE FUNCTION gds_graph_project(varchar, varchar, varchar);

-- Create service function to run `graph project`
DROP FUNCTION IF EXISTS gds_graph_list();
CREATE FUNCTION gds_graph_list()
    RETURNS variant
    SERVICE=gds_session
  ENDPOINT=http
  AS '/graphList';


-- Create service function to run `graph drop`
DROP FUNCTION IF EXISTS gds_graph_drop(varchar);
CREATE FUNCTION gds_graph_drop(GraphName varchar)
    RETURNS variant
    SERVICE=gds_session
  ENDPOINT=http
  AS '/graphDrop';

-- Create a service function that allows writing node properties from GDS back to a table
DROP FUNCTION IF EXISTS gds_write_nodeproperty(varchar, varchar, varchar, varchar);
CREATE FUNCTION gds_write_nodeproperty(GraphName varchar, NodeProperty varchar, ResultTable varchar, NodePropertyType varchar)
    RETURNS variant
    SERVICE=gds_session
  ENDPOINT=http
  AS '/writeNodeProperty';

-- Create WCC function
DROP FUNCTION IF EXISTS gds_wcc_mutate(varchar, varchar);
CREATE FUNCTION gds_wcc_mutate(GraphName varchar, MutateProperty varchar)
    RETURNS variant
    SERVICE=gds_session
  ENDPOINT=http
  AS '/wccMutate';

-- Create pagerank function
DROP FUNCTION IF EXISTS gds_pagerank_mutate(varchar, varchar);
CREATE FUNCTION gds_pagerank_mutate(GraphName varchar, MutateProperty varchar)
    RETURNS variant
    SERVICE=gds_session
  ENDPOINT=http
  AS '/pagerankMutate';
-- ======================================================

-- Node table / relationship table

SELECT * FROM p2p_users;
SELECT * FROM p2p_trans_w_shared_card;

-- Construct a graph from node and relationship tables
-- ===================================================

SELECT gds_graph_project('my_graph', 'nodes', 'relationships');

SELECT gds_graph_list();

SELECT gds_graph_drop('my_graph');

-- re-project for further demo
SELECT gds_graph_project('my_graph', 'p2p_users', 'p2p_trans_w_shared_card');

-- Weakly Connected Components (WCC)
-- =====================================================
SELECT gds_wcc_mutate('my_graph', 'component');
-- Write  to table
SELECT gds_write_nodeproperty('my_graph', 'component', 'COMMUNITIES', 'LONG');
SELECT * FROM communities;

-- PageRank
-- =====================================================
SELECT gds_pagerank_mutate('my_graph', 'scores');
-- Write  to table
SELECT gds_write_nodeproperty('my_graph', 'scores', 'P2P_Pagerank_Score', 'DOUBLE');
-- Query result from table
SELECT * FROM p2p_pagerank_score;

-- ======================================================

-- Show GDS features merged
SELECT p2p_users.nodeId, p2p_users.FraudMoneyTransfer, p2p_users.ipNumber, p2p_users.cardNumber, p2p_users.deviceNumber,
       vals.node, vals.wccId, vals.pagerank
FROM p2p_users JOIN (SELECT communities.node AS cnode, communities.value AS wccId, p2p_pagerank_score.node, p2p_pagerank_score.value AS pagerank FROM communities INNER JOIN p2p_pagerank_score ON cnode = p2p_pagerank_score.node) vals
                    ON p2p_users.nodeId = vals.node
ORDER BY wccId;



-- show =aggregated features by resolved entity Id
SELECT LISTAGG(p2p_users.nodeId), SUM(p2p_users.FraudMoneyTransfer) AS fraudFalgs, vals.wccId, SUM(vals.pagerank)
FROM p2p_users JOIN (SELECT communities.node AS cnode, communities.value AS wccId, p2p_pagerank_score.node, p2p_pagerank_score.value AS pagerank FROM communities INNER JOIN p2p_pagerank_score ON cnode = p2p_pagerank_score.node) vals
                    ON p2p_users.nodeId = vals.node
GROUP BY wccId ORDER BY fraudFalgs DESC




