# The Elasticsearch Tutorial: Part 2, Vector Search

Last Updated: _2024-02-25_

---

These will be a continuation of notes from doing the [elasticsearch tutorial](https://www.elastic.co/search-labs/tutorials/search-tutorial/welcome).  This will be written as I go so that you can go on this `journey` with me.

What am I going to learn this time?  According to the tutorial:

> - This section will introduce you to a different way of searching that leverages Machine Learning (ML) techniques to interpret meaning and context.

Last time I learned some basic querying techniques which ultimately used regex-style matching and filtering; it seems that this time I'll be doing some sweet, sweet machine learning!

<figure>
    <img src="../assets/images/elasticsearch-tutorial-02_decision_tree.jpg"
         alt="A decision tree.">
    <figcaption>A decision tree.</figcaption>
</figure>

## Embeddings

The tutorial defines the term **embedding** as

> a vector (an array of numbers) that represents real-world objects such as words, sentences, images or videos.

There'll no doubt be some examples soon if you haven't seen this kind of thing before.  One cool thing you can do with embeddings is define and then calculate **distances** between them.  This is done in a similar way as you might do in school:

$$
\begin{array}{ll}
A &= (0, 0, 1)\\\\
B &= (0, 1, 0)\\\\
d(A, B) &= \sqrt{(0 - 0)^2 + (0 - 1)^2 + (1 - 0)^2} = \sqrt{2}\\\\
\end{array}
$$

For \\(d(A, B)\\) I used a Euclidean distance, but any [distance function](https://en.wikipedia.org/wiki/Distance#Mathematical_formalization) would work equally well.

Why do I care about finding the distances between embeddings?  This might tell them if the two terms (or pictures, or videos, or whatever) are _similar_ to each other in some respect.

The tutorial goes on and tells me that I'll use embeddings to help find concepts that are similar to one-another instead of using the keyword searching I've been doing so far.

## Generating Embeddings

As soon as I get onto the next page of the tutorial, it tells me to go install [SentenceTransformers](https://www.sbert.net/).  I've heard of this before but haven't worked with it.

The tutorial tells me to select a pre-trained model.  Sure, that's reasonable, I don't want to have to spend all my time training this thing &mdash; and I almost certainly don't have enough data to train it on!  The tutorial recommends the `all-MiniLM-L6-v2` model on [huggingface](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2) and I have no strong opposition.

<figure>
    <img src="../assets/images/elasticsearch-tutorial-02_model_tags.png"
         alt="Model Tags.">
    <figcaption>Wow, trivia qa <b>and</b> yahoo answers?</figcaption>
</figure>

I create a new python file in my Elasticsearch toy folder and copy their code down to load the model:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
```

Running the code gives me a bunch of logs of things downloading which I assume must be the model, or something equally magical.  I'm now able to generate embeddings!

```python
embedding = model.encode('The quick brown fox jumps over the lazy dog')
print(embedding)
```

I take a sip of water and check the output.

```text
[ 3.54967788e-02  6.12862594e-02  5.26920781e-02
  ...
  (A ton of rows!)
  ...
  3.31014022e-02 -3.06695923e-02    8.67674053e-02]
```

Oh, wow.  Taking a look at the model page again, I notice

> This is a sentence-transformers model: It maps sentences & paragraphs to a 384 dimensional dense vector space and can be used for tasks like clustering or semantic search.

That tracks.  The model has 384 dimensions, so this embedding will be an array with 384 elements.

## Field Types

This part of the tutorial goes into how ES tries its best to create field mappings in the index that make sense &mdash; like the "text" and "date" fields in the previous section &mdash; but that I can explicitly create fields with a certain type if I want.  They give the code for that here:

```python
class Search:
    # ...

    def create_index(self):
        self.es.indices.delete(index='my_documents', ignore_unavailable=True)
        self.es.indices.create(index='my_documents', mappings={
            'properties': {
                'embedding': {
                    'type': 'dense_vector',
                }
            }
        })
```

Notice that the embedding type is _dense vector_.  I thought to myself: what _is_ a dense vector?  It turns out that this is the opposite of a _sparse vector_: whereas a sparse vector primarily consists of zero entries with only a few non-zero entries, a dense vector contains a large number of non-zero entries.  Given the vector above is mostly non-zero entries, it makes sense that this embedding will pop out dense vectors and, therefore, this embedding type makes sense for my index.

There's a few optional parameters that I can set if I want: `dims` (the dimension of the vector), `index` (vectors should be indexed for searching), and `similarity` (the distance function to use, where `cosine` and `dot_product` are the most common).

In almost exactly the same way I was able to upload my documents when I did the "Full-Text" tutorial, I'm able to upload my embeddings.  Code from the tutorial:

```python
class Search:
    # ...

    def get_embedding(self, text):
        return self.model.encode(text)

    def insert_document(self, document):
        return self.es.index(index='my_documents', document={
            **document,
            'embedding': self.get_embedding(document['summary']),
        })

    def insert_documents(self, documents):
        operations = []
        for document in documents:
            operations.append({'index': {'_index': 'my_documents'}})
            operations.append({
                **document,
                'embedding': self.get_embedding(document['summary']),
            })
        return self.es.bulk(operations=operations)
```

I haven't mentioned this yet, but it does bother me that there are no type-hints in this code.  On one hand I understand it could be a bit distracting but on the other hand I like to know what types my parameters are.  It helps me understand the "flow" of the code.  Alas, life isn't fair sometimes.

## k-Nearest Neighbor Search

If you haven't seen kNN before, I've drawn this picture _just for you_.  

<figure>
    <img src="../assets/images/elasticsearch-tutorial-02_knn.png"
         alt="kNN.">
    <figcaption>The black circle is the "new" thing to be classified.  If k = 3, look at the 3 nearest neighbors to the black dot: pink, green, green.  Since there are more greens, the black dot is classified as green.  If, on the other hand, k = 7, then looking at the 7 nearest neighbors (all of the other dots) give us 5 pink and 2 green: in this case, the black dot is classified as green.  It is important to pick the right k for the job, and that's not always easy!</figcaption>
</figure>

Luckily, ES is going to do the work for me.  By default, ES will use [cosine similarity](https://en.wikipedia.org/wiki/Cosine_similarity) as the distance function and find all of the embeddings close to whatever the query is with respect to that distance function.  ES has kNN as part of the [default search API](https://www.elastic.co/guide/en/elasticsearch/reference/current/search-search.html#search-api-knn).

## Hybrid Search

This section talks about [Reciprocal Rank Fusion](https://www.elastic.co/guide/en/elasticsearch/reference/current/rrf.html).  Seems like a fancy polling-type thing where a few different result sets can be compared.  The algorithm is suprisingly simple:

```python
score = 0.0
for q in queries:
    if d in result(q):
        score += 1.0 / ( k + rank( result(q), d ) )
return score

# where
# k is a ranking constant
# q is a query in the set of queries
# d is a document in the result set of q
# result(q) is the result set of q
# rank( result(q), d ) is d's rank within the result(q) starting from 1
```

I don't have a great image in my head of what this does or why it works yet but popping in a few numbers convinces me it's at least directionally reasonable.

The way to use this is remarkably easy.  Check out [[this GET payload](https://www.elastic.co/guide/en/elasticsearch/reference/current/rrf.html#rrf-api)] example:

```json
{
    "query": {
        "term": {
            "text": "shoes"
        }
    },
    "knn": {
        "field": "vector",
        "query_vector": [1.25, 2, 3.5],
        "k": 50,
        "num_candidates": 100
    },
    "rank": {
        "rrf": {
            "window_size": 50,
            "rank_constant": 20
        }
    }
}
```

> In the above example, we first execute the kNN search to get its global top 50 results. Then we execute the query to get its global top 50 results. Afterwards, on a coordinating node, we combine the knn search results with the query results and rank them based on the RRF method to get the final top 10 results.

Text search, kNN, and RRF all working together like one big happy family.  Cool stuff, ES.

## Next Time

I didn't do much "hands on" work this time since the kNN + RRF were quite similar to the full-text search in terms of the API and it was a bit more boring than I thought to bulk upload a bunch of sample embeddings and see which were close to one-another.  I'm sure if I had a better dataset than "random phrases I thought of" it would be neat.  Maybe in the last part of this series I'll find a nice dataset and answer some questions in it.

The "Vector Search" part of the ES tutorial ends here.  In the next post I'll cover the next part of the tutorial: Semantic Search.  This is the part with that ELSER Model, so I'll finally get to learn what the acronym stands for!
