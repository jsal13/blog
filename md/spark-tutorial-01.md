# Apache Spark Tutorial: Part 1, 

<!-- ID: 202403060010 -->
Last Updated: _2024-03-06_

---

Spark is a "unified analytics engine for large-scale data processing" and, odds are, if you've worked in the data space you've heard about it.  I've used Spark a little in the past but, **for the purposes of this blog post I will act as if I don't know much about it so that you, the reader, can learn along with me.**

I'll work with [this documentation](https://spark.apache.org/docs/latest/api/python/getting_started/index.html) from the Apache Spark website itself.  I'll go over most of the Quickstart stuff, then see what else I want to do.  **Most of the time that I say "Spark", I'll be viewing it through the lense of using PySpark to communicate with it.**

## What Do I Know About Spark Already?

If I'm going to be querying or transforming data, my rule of thumb is:

- **Small Data** (data that can fit in memory on whatever machine I'm using), use **Polars/Pandas**.
- **Medium Data** (data that can't fit in memory but _can_ fit on disk), use **Dask**.
- **Big Data** (data that can't fit in memory or on my local machine's disk), use **Spark**.

Since my work has been mainly with small and medium data, with "samples of big data" often being good enough, I haven't needed to write many Spark jobs.  The ones I have written are mainly of the form: we have a ton of data in a [data lakehouse](https://cloud.google.com/discover/what-is-a-data-lakehouse) and we need to take a bunch of that data, transform it somehow, and maybe join it with some other data.  I'm sure there are other workflows but this is the one I'm used to.

## Docker Saving The Day

I do not want to try installing Spark on my laptop.  I've had to do it in the past and it is painful. Luckily, Docker is there for me!  I pull down Spark with a nice [Jupyter-created image](https://quay.io/repository/jupyter/pyspark-notebook?tab=tags):

```shell
docker pull quay.io/jupyter/pyspark-notebook:python-3.11
```

Reading [the documentation](https://jupyter-docker-stacks.readthedocs.io/en/latest/index.html), it looks like this is how I ought to run the image:

```shell
docker run -it --rm \
    -p 10000:8888 \
    -v "${PWD}":/home/jovyan/work \
     quay.io/jupyter/pyspark-notebook:python-3.11
```

The `-v` flag mounts the current directory which allows the work I'm doing to persist after the docker container is terminated.

I create the container and everything looks good.  Let's go to the first Quickstart tutorial.

## Quickstart: DataFrame

The [DataFrame quickstart](https://spark.apache.org/docs/latest/api/python/getting_started/quickstart_df.html) begins by going over a few important details which I'll recount here:

- DataFrame are _lazily evaluated_.  I prefer the term _call-by-need_ for this, but either way the idea is that the expression (or, in this case, the DataFrame) isn't evaluated until it's needed.

- Similarly, when Spark "transforms" data it does not do so _immediately_ but, rather, plans how to compute the transform for later; it saves the computation for when certain things are explicitly called by the user.

The quickstart also notes that DataFrames are implemented on top of RDDs, which the linked page gives us the definition of:

> The main abstraction Spark provides is a resilient distributed dataset (RDD), which is a collection of elements partitioned across the nodes of the cluster that can be operated on in parallel.

I'm not going to worry much about this detail in this blog post but it's nice to know.

To begin, I need to create a `SparkSession`, which acts sort of like a command center: it connects PySpark to all the stuff in my Spark cluster.  According to [this page](https://sparkbyexamples.com/spark/sparksession-explained-with-examples/), `SparkSession` was created when some of the other contexts (SQL, Hive, Streaming, etc.) were smashed together.  In any case, I need to define this to continue:

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()
```

Creating a Spark DataFrame is similar to Pandas but is a method of my `SparkSession` object and has a weird lowerCamelCase function name: `createDataFrame()`.

```python
from datetime import datetime, date
from pyspark.sql import Row

df = spark.createDataFrame([
    Row(a=1, b=2., c='str1', d=date(2000, 1, 1), e=datetime(2000, 1, 1, 12, 0)),
    Row(a=2, b=3., c='str2', d=date(2000, 2, 1), e=datetime(2000, 1, 2, 12, 0)),
    Row(a=4, b=5., c='str3', d=date(2000, 3, 1), e=datetime(2000, 1, 3, 12, 0))
])
df
```

The `Row` [objects](https://spark.apache.org/docs/3.1.3/api/python/reference/api/pyspark.sql.Row.html) seem to function like dataclass objects; I'm sure they do some important stuff under-the-hood but I'm not going to worry about it right now.

One important thing I notice: this does _not_ return the data when I call `df`: it returns the _schema_, which makes sense since I know that DataFrames are lazily evaluated.

Making a DataFrame from pandas is pretty easy: `df = spark.createDataFrame(pandas_df)`.  Fairly straight-forward there.

I can print out the values and the schema explicitly with the `.show()` and `.printSchema()` methods:

```raw
df.show(3)
df.printSchema()

+---+---+-------+----------+----------------+
|  a|  b|      c|         d|               e|
+---+---+-------+----------+----------------+
|  1|2.0|str1|2000-01-01|2000-01-01 12:00:00|
|  2|3.0|str2|2000-02-01|2000-01-02 12:00:00|
|  3|4.0|str3|2000-03-01|2000-01-03 12:00:00|
+---+---+-------+----------+----------------+

root
 |-- a: long (nullable = true)
 |-- b: double (nullable = true)
 |-- c: string (nullable = true)
 |-- d: date (nullable = true)
 |-- e: timestamp (nullable = true)
```

They give a few tips and tricks (`df.show(1, vertical=True)` gives a vertical view, `.columns` gives a list of columns, `.describe().show()` gives min, max, stdev, count, and mean of each column).  This will become important when we get our hands dirty but, for now, it's one of those things I'll put in the back of my head and "remember" that it exists later so I can look up the syntax.  

Getting the data from Spark is easy: I can use `.collect()` to get everything, `.tail(n)` to take `n` rows from the end, `.toPandas()` to convert the Spark DataFrame to a Pandas DataFrame.

TODO: Do I really want to do this one?  It's just rehashing the tutorial.  I think maybe doing a project would be better.
<!-- ## Next Time

The next thing that the tutorial recommends doing is a [Chatbot Tutorial](https://www.elastic.co/search-labs/tutorials/chatbot-tutorial/welcome).  Since this tutorial goes over the [Langchain](https://www.langchain.com/) project and works with some concepts I'm not familiar with, I think it might be fun to try out.

See you there! -->
