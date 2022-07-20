# Integration step-by-step tutorial

I prepared several tools for this. All tools/files are located in root directory of this project. In case of any issues do no hesitate to contact me.

## 1. Start services

All services used for this project are described in [docker-compose.yaml](docker-compose.yaml) file.
Run the following command to start all services.

```bash
docker compose up -d
```

After all services are up, you can check following links:
* MindsDB - [http://127.0.0.1:47334/](http://127.0.0.1:47334/)
* GoodData.CN - [http://localhost:3000/](http://localhost:3000/)

Credentials for GoodData.CN are:
* username: demo@example.com
* password: demo123
* token (for REST APIs or SDKs): YWRtaW46Ym9vdHN0cmFwOmFkbWluMTIz

## 2. Check MindsDB, GoodData.CN content (optional)

See [MindsDB Documentation](https://docs.mindsdb.com/) and [GoodData.CN Documentation](https://www.gooddata.com/developers/cloud-native/doc/) or [GoodData University](https://university.gooddata.com/page/gooddatacn) for further overview.

## 3. Connect to GoodData FDW and import insights

GoodData FDW is an exposed Postgres database that allows you to expose data from GoodData.CN and consume them by other data consumers.
To connect to GoodData FDW, I recommend using a database manager. For the purpose of this demo [DBeaver](https://dbeaver.io/) was used.

The GoodData FDW is accessible with the following settings:
* host: localhost
* port: 2543
* username: gooddata
* password: gooddata123
* database: gooddata

Executes the following command to create a connection with GoodData.CN instance.

```sql
CREATE SERVER multicorn_gooddata FOREIGN DATA WRAPPER multicorn
  OPTIONS (
    wrapper 'gooddata_fdw.GoodDataForeignDataWrapper',
    host 'http://gooddata-cn-ce:3000',
    token 'YWRtaW46Ym9vdHN0cmFwOmFkbWluMTIz',
    headers_host 'localhost'
  );
```
To import insights to the Postgres database execute the following command:
```sql
CALL import_gooddata(workspace := 'demo', object_type := 'insights');
```
After these steps, you should be able to access insight revenue in time from the Postgres database.
Let us try to query it!
```sql
SELECT * FROM gooddata.demo.revenue_in_time;
```

# 4. MindsDB

First, we need to add the data source we want to work with. We will add GoodData FDW set in the previous step using the following command:

```sql
CREATE DATABASE fdw_gooddata
    WITH ENGINE = "postgres",
    PARAMETERS = {
        "user": "gooddata",
        "password": "gooddata123",
        "host": "gooddata-fdw", 
        "port": "5432",
        "database": "gooddata"
};
```
Let us check if the data source was added successfully.

```sql
SELECT * FROM fdw_gooddata.demo.revenue_in_time;
```

Now we are ready to create a predictor. We want to predict revenue for each category in time.
Month time granularity is used. We create a predictor using the following command:

```sql
CREATE PREDICTOR mindsdb.forecast_revenue
FROM fdw_gooddata
(SELECT date_month, region, revenue FROM demo.revenue_in_time)
PREDICT revenue

ORDER BY date_month
GROUP BY region

WINDOW 50 -- specifies the number of rows to "look back" into when making a prediction
HORIZON 12; -- specifies the number of future predictions
```

The command triggers training. We can check the progress of the predictor in the following table. We are waiting for the predictor's status to be completed.

```sql
SELECT *
FROM mindsdb.predictors
WHERE name = 'forecast_revenue';
```

When training of the predictor is finished. Let us show the forecast of revenue for the South region.

```sql
SELECT m.date_month as date,
m.revenue as revenue
FROM mindsdb.forecast_revenue as m
JOIN fdw_gooddata.demo.revenue_in_time as t
WHERE t.date_month > LATEST AND t.region = 'South'
LIMIT 4;
```

As we can see, we can receive a forecast for the South region. Let us visualize it back in GoodData. For that purpose, we will create a table in GoodData FDW with predictions.

```sql
CREATE OR REPLACE TABLE fdw_gooddata.demo.forecast (
    SELECT m.date_month, 
           m.revenue as prediction, 
           m.region, 
           t.revenue as revenue 
           FROM mindsdb.forecast_revenue as m 
    JOIN fdw_gooddata.demo.revenue_in_time as t
);
```

# 5. Predictions in GoodData FDW

Let us check that the forecast table was created back in GoodData FDW.

```sql
SELECT * FROM gooddata.demo.forecast f;
```

We can see that the structure of imported predictions is not ideal. Let us create a view that we can use back in visualization.

```sql
CREATE OR REPLACE 
VIEW demo.revenue_forecast AS
SELECT
    CAST(f."forecast_revenue.date_month"  AS DATE) AS date_month,
    f."forecast_revenue.region" AS region,
    f.revenue AS revenue ,
    CASE
        WHEN revenue IS NULL THEN f."forecast_revenue.revenue"
        ELSE NULL
        END AS forecast
FROM
    gooddata.demo.forecast f
WHERE
    f."forecast_revenue.region" IS NOT NULL;
```

# 6. Visualization of predictions in GoodData.CN

There is a workspace named prediction back in GoodData.CN contains a metric "Revenue join," joining past and predicted revenue together, insight showing past revenue and predicted revenue.

![Visualization of past and predicted revenue](content/images/prediction_insight.png)



