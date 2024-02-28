# The Elasticsearch Tutorial: Part 3, Semantic Search using ELSER

<!-- ID: 0030 -->
Last Updated: _2024-02-26_

---

These will be a continuation of notes from doing the [elasticsearch tutorial](https://www.elastic.co/search-labs/tutorials/search-tutorial/welcome).  This will be written as I go so that you can go on this `journey` with me.

What am I going to learn this time?  According to the tutorial:

> In this section you are going to learn about another Machine Learning approach to search that utilizes the Elastic Learned Sparse EncodeR model, or ELSER, a Natural Language Processing model trained by Elastic to perform semantic search.

Last time(s) I learned the basic full-text search as well as some ML searching (with kNN).  There was also a tiny section on how to combine them with a thing called RRF.  This time it looks like I'm going to jump down the NLP rabbit-hole and learn something called ELSER which &mdash; despite my "very good" acronym deduction skills &mdash; does not begin with "**EL**astic **S**earch".  I'll get'em next time.

<!-- <figure>
    <img src="../assets/images/elasticsearch-tutorial-02_decision_tree.jpg"
         alt="A decision tree.">
    <figcaption>A decision tree.</figcaption>
</figure> -->

## The ELSER Model

Remember `dense_vector`s?  They were the opposite of sparse vectors (lots of non-zero entries).  Typically the criticism lobbied against `dense_vectors` is that there's no great way to compress them so you wind up having to use a ton of space to represent them.  Sometimes, it's _Good Enough &trade;_ to try and find the "important" or "most influential" dimensions in the vector and use those.  What's nice about this is that, instead of having a ton of elements to work with you'll only have a few.  Moreover, you can do some fairly easy compression on!  For example,

```python
import numpy as np

# Make a dense vector where every entry is very small
# except for a few spots where it's large.
# This is hard to compress!  How would *you* do it and
# still retain all the information?
dense_vector = 0.001 * np.random.rand(50000)
for idx in [5, 10, 15, 20, 25]:
    dense_vector[idx] = idx + 2

# If, on the other hand, I don't care ab out the very small
# values, and map them to 0...
sparse_vector = dense_vector.copy()
sparse_vector[sparse_vector < 0.01] = 0

# Every element in the sparse vector is 0 except the indexes above:

print(sparse_vector[:50])
# array([
#   0., 0., 0., 0., 0., 7., 0., 0., 
#   0., 0., 12., 0., 0., 0., 0., 17.,
#   0., 0., 0., 0., 22., 0., 0., 0.,
#   0., 27., 0., 0., 0., 0., 0., 0.,
#   0., 0., 0., 0., 0., 0., 0., 0., 
#   0., 0., 0., 0., 0., 0., 0., 0., 
#   0., 0.
#])

# This can be represented in a more condensed form
# with a simple mapping with `idx: value`!

sparse_vector_condensed = {
    5: 7, 
    10: 12, 
    15: 17
    20: 22,
    25: 27
}
```

This can be slimmed down some more, but the point is that a lot of space can be saved with this.  Moreover, it's a simple exercise to define things like dot products or even matrix operations for sparse matricies.  Neato.

Enough of me gushing about sparse vectors, let me get back to the tutorial at hand.

In the same way I added dense vectors to the index, I can also add some sparse vectors ("`elser_embeddings`"):

```python
class Search:
    # ...

    def create_index(self):
        self.es.indices.delete(index='my_documents', ignore_unavailable=True)
        self.es.indices.create(index='my_documents', mappings={
            'properties': {
                'embedding': {
                    'type': 'dense_vector',
                },
                'elser_embedding': {
                    'type': 'sparse_vector',
                },
            }
        })
    
    # ...
```

The ELSER model needs to be downloaded, similar to the way that I had to download that other embedding model.  As per the tutorial:

```python
class Search:
    # ...

    def deploy_elser(self):
        # download ELSER v2
        self.es.ml.put_trained_model(model_id='.elser_model_2',
                                     input={'field_names': ['text_field']})
        
        # wait until ready
        while True:
            status = self.es.ml.get_trained_models(model_id='.elser_model_2',
                                                   include='definition_status')
            if status['trained_model_configs'][0]['fully_defined']:
                # model is ready
                break
            time.sleep(1)

        # deploy the model
        self.es.ml.start_trained_model_deployment(model_id='.elser_model_2')

        # define a pipeline
        self.es.ingest.put_pipeline(
            id='elser-ingest-pipeline',
            processors=[
                {
                    'inference': {
                        'model_id': '.elser_model_2',
                        'input_output': [
                            {
                                'input_field': 'summary',
                                'output_field': 'elser_embedding',
                            }
                        ]
                    }
                }
            ]
        )
```

So far, things seem quite similar to the other embedding which is most likely on purpose.  I appreciate it, makes it easier to pick up, learn, and remember!

The `.put_trained_model()` method downloads ELSER.  The `.start_trained_model_deployment()` method, guess what, will begin the deployment of the model.

The last thing the tutorial does here is to "define a pipeline" for it to tell ES how to use the model.  This is the `.put_pipeline()` method.  This probably becomes much more complex as the pipelining in and out of the model become full of weird business logic stuff, but for now it's nice and simple: summary in, model output out.  But _what is the model output?_  I guess I'll see soon.

The index needs to know about the pipeline and the way to add the pipeline to the index is straight-forward:

```python
class Search:
    # ...

    def create_index(self):
        self.es.indices.delete(index='my_documents', ignore_unavailable=True)
        self.es.indices.create(
            index='my_documents',
            mappings={
                'properties': {
                    'embedding': {
                        'type': 'dense_vector',
                    },
                    'elser_embedding': {
                        'type': 'sparse_vector',
                    },
                }
            },
            settings={
                'index': {
                    'default_pipeline': 'elser-ingest-pipeline'
                }
            }
        )
```

_Why_ does the index need to know about the pipeline?  At this point, I realized my understanding of what the index _is_ might not be the best, so I [looked it up](https://www.elastic.co/blog/what-is-an-elasticsearch-index).  Some relevant parts of this linked blog entry:

> An Elasticsearch index is a logical namespace that holds a collection of documents, where each document is a collection of fields — which, in turn, are key-value pairs that contain your data.

> Elasticsearch indices are not the same as you’d find in a relational database. Think of an Elasticsearch cluster as a database that can contain many indices you can consider as a table, and within each index, you have many documents.

> RDBMS => Databases => Tables => Columns/Rows

> Elasticsearch => Clusters => Indices => Shards => Documents with key-value pairs

Right, the ELSER output will be a _sparse vector_, so this is the value in a key-value pair associated with a document.  That way, I can compare "closeness" of documents in a similar way that I did with the dense vectors.

The ES tutorial notes:

> Spend some time experimenting with different searches. You will notice that as with dense vector embeddings, searches driven by the ELSER model work better than full-text search when the exact words do not appear in the indexed documents.

Reasonable!  If the text doesn't appear in the document, how would full-text search know about it?  One lingering question in my mind: _how does ELSER compare with the previous ML (kNN) approach with dense vectors?_

Often, different approaches will work on different problems.  I don't have a handle on exactly which problems are good for which approach right now.  Maybe I'll learn that soon &mdash; or maybe I'll have to wait for a lifetime of experience to be able to figure it out.  Somewhere in that range.

## Semantic Queries & Hybrid Search

These next two pages are virtually identical to the previous ML (kNN, RRF) part of the tutorial so I skim them.  The Hybrid Search part has an important caveat:

> The complication that is presented when trying to do the same to combine full-text and sparse vector search requests is that both use the query argument. To be able to provide the two queries that need to be combined with the RRF algorithm, it is necessary to include two query arguments, and the solution to do this is to do it with Sub-Searches.

> Sub-searches is a feature that is currently in technical preview. For this reason the Python Elasticsearch client does not natively support it.

There exists a work-around which I won't cover here since it will most likely become out-of-date or not necessary as sub-search is supported in a "Coming Soon!" version of ES.

## Next Time

The next thing that the tutorial recommends doing is a [Chatbot Tutorial](https://www.elastic.co/search-labs/tutorials/chatbot-tutorial/welcome).  Since this tutorial goes over the [Langchain](https://www.langchain.com/) project and works with some concepts I'm not familiar with, I think it might be fun to try out.

See you there!
