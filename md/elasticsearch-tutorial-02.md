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
