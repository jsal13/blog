# The Elasticsearch Tutorial: Part 1, Full Search

<!-- ID: 202402240010 -->
Last Updated: _2024-02-24_

---

These will be notes from doing the [elasticsearch tutorial](https://www.elastic.co/search-labs/tutorials/search-tutorial/welcome).  This will be written as I go so that you can go on this `journey` with me.

What am I going to learn?  According to the tutorial:

> - How to perform full-text keyword searches on a dataset, optionally with filters,
> - How to generate, store and search dense vector embeddings using a Machine Learning model,
> - How to use the ELSER model to generate and search sparse vectors,
> - How to combine search results from the methods listed above using Elastic's Reciprocal Rank Fusion (RRF) algorithm,

Huh, neat.  Full-text keyword searches is what I generally think of when I see Elastisearch, and I know very little about dense vector embeddings right now &mdash; let alone how I'd generate, store, and search them!  I have zero familiarity with the ELSER model but I'm guessing that the "ELS" is for "Elastic Search".  The RRF algorithm sounds vaguely like the page-rank algorithm but I'll see when I get to it.

## Setting Things up for the Tutorial

Since I'm using docker compose to run my local Elastisearch toy, I need to increase our Docker memory limit in WSL to 4GB, as per [this note](https://www.elastic.co/guide/en/elasticsearch/reference/8.12/docker.html#_configure_and_start_the_cluster).  The rest is easy: copy their `.env` and `docker-compose.yaml` file (on the same page as the note) and `docker compose up`.  After a few seconds I'm off to the races.

## The Starter Application

This tutorial has a pre-written [Starter Application](https://www.elastic.co/search-labs/tutorials/search-tutorial/starter-project), which means that I'm going to have to look through and investigate what this application does before I move on.  I might not wind up needing it.

It's a flask app which appears to function as a frontend for querying and getting results.  Since it's not something that I'm ever going to use after the tutorial I'm going to ignore most of it and run my own scripts instead.  However, they included a **JSON of sample data** where each record looks like this:

```json
{
  "content": "Effective: March 2020\nPurpose\n\n...",
  "name": "Work From Home Policy",
    "url": "./sharepoint/Work from home policy.txt",
    "created_on": "2020-03-01",
    "updated_at": "2020-03-01",
    "category": "teams",
    "rolePermissions": ["demo", "manager"]
}
```

I've truncated the string in "content" so it would fit here.  Awesome, sample data!

## Full-Text Search

Ah, this part goes over the ES _Python_ client, which is why they included a _Python_ flask sample app.  Makes sense.  I'll blaze my own path here since all I need is to write some code to query my local ES.  The endpoint to interact with my ES cluster is <localhost:9200>.

After making a tiny venv to use, I install the Python `elasticsearch` package.  Let's see what this little guy can do.  Following the tutorial with slight modifications, I try:

```python
from elasticsearch import Elasticsearch


class Search:
    def __init__(self):
        self.es = Elasticsearch("http://localhost:9200")
        client_info = self.es.info()
        print("Connected to Elasticsearch!")
        print(client_info.body)


es = Search()
```

This gives me the following response:

```text
elastic_transport.ConnectionError: Connection error caused by: ConnectionError
(Connection error caused by: ProtocolError (('Connection aborted.', 
RemoteDisconnected('Remote end closed connection without response'))))
```

Oh, I bet I need to use `https` to talk to ES.  Since I don't want to deal with all the certificate stuff right now, and since this is _not_ a production application, I went into the docker compose file and commented out everything that looked SSL-y to me.  I `docker compose up` and I'm good to go.

The same code now gives me:

```text
Connected to Elasticsearch!
{
  'name': 'es01',
  'cluster_name': 'docker-cluster',
  'cluster_uuid': 'quQ8sGbMRhO80D5nUlDRPw',
  'version': {'number': '8.12.1',
  'build_flavor': 'default',
  'build_type': 'docker',
  'build_hash': '6185ba65d27469afabc9bc951cded6c17c21e3f3',
  'build_date': '2024-02-01T13:07:13.727175297Z',
  'build_snapshot': False,
  'lucene_version': '9.9.2',
  'minimum_wire_compatibility_version': '7.17.0',
  'minimum_index_compatibility_version': '7.0.0'},
  'tagline': 'You Know, for Search'
}
```

Great!  The `elasticsearch.Elasticsearch()` class is a client class which takes a host as its first parameter. I can make sure it connected to a cluster with the `.info()` method.  

What's next?  Maybe we put in a document?

## Create an Index

The tutorial defines two important concepts here.

Roughly, a **document** is a collection of fields with their associated values and an **index** is a collection of documents.  What do they mean by "collection of fields with their associated values", though?  Is this like JSON?

> If you have worked with other databases, you may know that many databases require a schema definition, which is essentially a description of all the fields that you want to store and their types. An Elasticsearch index can be configured with a schema if desired, but it can also automatically derive the schema from the data itself.  

> In this section you are going to let Elasticsearch figure out the schema on its own, which works quite well for simple data types such as text, numbers and dates. Later, after you are introduced to more complex data types, you will learn how to provide explicit schema definitions.

So... sort of.  Let's see how it goes in practice.

```python
class Search:
    def __init__(self):
        ...

    def create_index(self):
        self.es.indices.delete(index='my_documents', ignore_unavailable=True)
        self.es.indices.create(index='my_documents')

es = Search()
es.create_index()
```

The `ignore_unavailable=True` functions like the `IF EXISTS` in SQL: if ES can't find the index it ignores the delete command.  After executing my code, the docker logs give me:

```text
{
  "@timestamp":"2024-02-24T07:51:59.436Z",
  "log.level": "INFO",
  "message":"[my_documents] creating index,
  cause [api],
  templates [],
  shards [1]/[1]",
...
```

That tells me that our index creation worked.  Let's add a document to this index.

```python
class Search:
    ...

    def insert_document(self, document):
        return self.es.index(index="my_documents", body=document)


es = Search()
es.create_index()

document = {
    "title": "Work From Home Policy",
    "contents": "The purpose of this full-time work-from-home policy is...",
    "created_on": "2023-11-02",
}
resp = es.insert_document(document=document)
print(resp["_id"])
```

This outputs the associated response ID and shows that it has, indeed, inserted our document into the index.  

Does the index now have an associated schema?  In the [docs](https://elasticsearch-py.readthedocs.io/en/v8.12.1/api/elasticsearch.html) it shows we can use `client.indices.get(index="*")` to get the Index API.  Let's try it out.

```python
class Search:
    ...
    
    def index_info(self):
        return self.es.indices.get(index="*")
```

Which returns the following:

```json
{
  "my_documents": {
    "aliases": {},
    "mappings": {
      "properties": {
        "contents": {
          "type": "text",
          "fields": {
            "keyword": {
              "type": "keyword",
              "ignore_above": 256
            }
          }
        },
        "created_on": {
          "type": "date"
        },
        "title": {
          "type": "text",
          "fields": {
            "keyword": {
              "type": "keyword",
              "ignore_above": 256
            }
          }
        }
      }
    },
  }
}
```

It looks like our fields are in `my_documents > mappings > properties`.  I'm not sure what the "keyword" property is, but it did get the date field right and everything else looks okay.  Let's move on.

The tutorial tells us that, while I _can_ ingest documents this way, realistically I will want to use the `bulk` method to ingest a bunch of documents at once.  Makes sense to me.  I'll plop it in the `Search` class:

```python
class Search:
    ...
    def insert_documents(self, documents):
            operations = []
            for document in documents:
                operations.append({'index': {'_index': 'my_documents'}})
                operations.append(document)
            return self.es.bulk(operations=operations)
```

The rest of this section is about how to use the flask app with all of this.  I'll ignore it since I'm not going to use the included flask app.

**All of the code up until now, minus some of the stuff that wasn't important:**

```python
import json

from elasticsearch import Elasticsearch


class Search:
    def __init__(self):
        self.es = Elasticsearch("http://localhost:9200")
        client_info = self.es.info()
        print("Connected to Elasticsearch!")
        print(client_info.body)

    def create_index(self):
        self.es.indices.delete(index="my_documents", ignore_unavailable=True)
        self.es.indices.create(index="my_documents")

    def insert_documents(self, documents):
        operations = []
        for document in documents:
            operations.append({"index": {"_index": "my_documents"}})
            operations.append(document)
        return self.es.bulk(operations=operations)


es = Search()
es.create_index()

with open("sample-data.json", "r", encoding="utf-8") as f:
    documents = json.load(f)
es.insert_documents(documents=documents)
```

Note that the `sample-data.json` is the data that was included in the tutorial's sample application.

## Search Basics

The search method will also sit in the `Search` class and looks like this:

```python
class Search:
    ...

    def search(self, **query_args):
        return self.es.search(index='my_documents', **query_args)
```

The only thing that I need to know is: _what do the query args look like?_  The [match query](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-match-query.html) is "baby's first query" for ES and the way it's written for the Python client is:

```python
es.search(
    query={
        'match': {
            'name': {
                'query': 'search text here'
            }
        }
    }
)
```

Running this returns a whole big JSON of things; the "hits" portion gives me what I want to see:

```json
"hits": {
  "total": {
    "value": 0, "relation": "eq"
  }, 
  "max_score": null, 
  "hits": []
}
```

Well, that makes sense, since "search text here" isn't going to match anything in my documents.  Since I'll be using the match query a bit, I decided to make it a method:

```python
class Search:
    ...

    def search(self, **query_args):
        return self.es.search(index="my_documents", **query_args)

    def match_search(self, text):
        return self.search(query={"match": {"name": {"query": text}}})
```

Running this with the query `"work from home"` gives me a huge output.  The fields for the response can be found [here](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-search.html#search-api-response-body), but it includes the text the search term was found in and the _document id_.  This document id can be used with `self.es.get(index='my_documents', id=id)` to return the document itself.

There is also a way to match queries in different fields called _multi\_match_.  The query looks like this:

```json
{
  "query": {
    "multi_match" : {
      "query":    "this is a test", 
      "fields": [ "subject", "message" ] 
    }
  }
}
```

The Python equivalent is how I expected it to look, similar to our above match query.

## Pagination

Everyone's _favorite_: pagination.  Frustrating to keep track of, annoying when it errors out.  Luckily, it's not too bad here:

```python
results = es.search(
    query={
        'multi_match': {
            'query': query,
            'fields': ['name', 'summary', 'content'],
        }
    }, size=5, from_=5
)
```

Similar to how I'd expect it, with the exception of the underscore in `from_`.

Not much else going on here, so I'll move on.

## Boolean Queries and Filtering

The structure of the booleans, even after reading the tutorial page, was a bit fuzzy to me.  I looked up [an example](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-bool-query.html) which gives the gist of it:

```json
{
  "query": {
    "bool" : {
      "must" : {
        "term" : { "user.id" : "kimchy" }
      },
      "filter": {
        "term" : { "tags" : "production" }
      },
      "must_not" : {
        "range" : {
          "age" : { "gte" : 10, "lte" : 20 }
        }
      },
      "should" : [
        { "term" : { "tags" : "env1" } },
        { "term" : { "tags" : "deployed" } }
      ],
      "minimum_should_match" : 1,
      "boost" : 1.0
    }
  }
}
```

Looks complicated at first, but if we cut out some of the outer fields it becomes a bit easier to read.  Everything is nested in the `query > bool` fields, so I'll get rid of those:

```json
"must" : {
    "term" : { "user.id" : "kimchy" }
},
"filter": {
    "term" : { "tags" : "production" }
},
"must_not" : {
    "range" : {
        "age" : { "gte" : 10, "lte" : 20 }
    }
},
"should" : [
    { "term" : { "tags" : "env1" } },
    { "term" : { "tags" : "deployed" } }
],
"minimum_should_match" : 1,
"boost" : 1.0
```

According to the tutorial, there's four different ways to combine queries:

- `bool.must`: the clause must match. If multiple clauses are given, all must match (similar to an AND logical operation).
- `bool.should`: when used without must, at least one clause should match (similar to an OR logical operation). When combined with must each matching clause boosts the relevance score of the document.
- `bool.filter`: only documents that match the clause(s) are considered search result candidates.
- `bool.must_not`: only documents that do not match the clause(s) are considered search result candidates.

According to this, the above tells us:

- The results _must_ have the `user.id` match `kimchy`,
- The filter will only include documents with `tags` containing `production`,
- The results _should_ have `tags` containing at least one of `env1` or `deployed`, and if they contain both then it boosts that document's relevance score.  
- The reference page tells me, "You can use the minimum_should_match parameter to specify the number or percentage of should clauses returned documents must match.  If the bool query includes at least one should clause and no must or filter clauses, the default value is 1. Otherwise, the default value is 0."
- `boost` refers to how much a document should be boosted when it s boosted (eg, it has more than one "should"),
- The results _must not_ have an `age`in that range.

Reasonable enough!  This summarizes the querying in this section of the tutorial.  The only other thing they go over is the [match_all](https://www.elastic.co/guide/en/elasticsearch/reference/current/query-dsl-match-all-query.html) query which, as you might imagine, matches every document.  This is useful if, for example, only a filter is selected and we want to filter through all the documents instead of looking for matches.

## Aggregation

The last part of the Vector Search section is about "Faceted Search" which is a pattern where users search something and when the result is returned the user is presented with a list of _suggested filters_ which they can add to the query.

For example, if the user searched "work from home policy" then the results may contain articles from 2018, 2019, 2020, etc.  The user can be shown these years so that they can opt to choose one or more of these to further filter documents.

The most important part here for me right now is the _aggregation_.  It's easy to understand ES's [Terms Aggregation](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-aggregations-bucket-terms-aggregation.html) with an example, which I copy from that link:

```json
{
  "aggs": {
    "genres": {
      "terms": { "field": "genre" }
    }
  }
}
```

```json
{
  "aggregations": {
    "genres": {
      "doc_count_error_upper_bound": 0,   
      "sum_other_doc_count": 0,           
      "buckets": [                        
        {
          "key": "electronic",
          "doc_count": 6
        },
        {
          "key": "rock",
          "doc_count": 3
        },
        {
          "key": "jazz",
          "doc_count": 2
        }
      ]
    }
  }
}
```

In `aggregations > genres` there's a bunch of keys along with the number of docs containing those keys.  Notice I didn't do any filtering or boolean stuff in the query but I could have and that would have made the aggregation only count those results.  It feels close to using `GROUP BY` and `COUNT()` in SQL.

## Next Time

The "Full-Text Search" part of the ES tutorial ends here.  In the next post I'll cover the next parts of the tutorial: Vector Search and Semantic Search, as well as whatever might come out of those that piques my interest.
