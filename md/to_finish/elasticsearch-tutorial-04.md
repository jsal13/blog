# The Elasticsearch Tutorial: Part 4, Getting My Hands Dirty

<!-- ID: 202402240040 -->
Last Updated: _2024-02-26_

---

These will be a continuation of notes from doing the [elasticsearch tutorial](https://www.elastic.co/search-labs/tutorials/search-tutorial/welcome).  This will be written as I go so that you can go on this `journey` with me.

This time I'm going to do something a little different: I'm going to try out all of the things I've learned over the past few posts with some sample data and see what problems I run into.

## Parsing the Sample Data

I had the **Reuters-21578 Text Categorization Collection** ([link](https://kdd.ics.uci.edu/databases/reuters21578/reuters21578.html)) saved in my bookmarks and it seems like the perfect time to download it and check it out.  The description of the dataset tells us:

> This is a collection of documents that appeared on Reuters newswire in 1987. The documents were assembled and indexed with categories.

Unzipping the dataset with `tar -xvzf` (having to look up the flags for the millionth time), we find a whole bunch of text files and... `.sgm` files?  What in the world is an `sgm` file?

<figure>
    <img src="../assets/images/elasticsearch-tutorial-04_sgm.png"
         alt="SGM">
    <figcaption>What in the world is an "sgm" file?  And... is that a "dtd" file I see?</figcaption>
</figure>

Luckily, there's a README included which, first, tells me to cite the dataset:

> The Reuters-21578, Distribution 1.0 test collection is available
from David D. Lewis' professional home page, currently: <http://www.research.att.com/~lewis>

Next, the README describes, in a lengthy bunch of sections, what "SGML" is and how to parse the `sgm` files.  There's a lot here but it sort of looks like XML so I'm just going to open one of the files and see what happens.  Here's what each of the sections looks like (body abbreviated with [...] by me):

```xml
<REUTERS TOPICS="YES" LEWISSPLIT="TRAIN" 
    CGISPLIT="TRAINING-SET" OLDID="5544" NEWID="1">
<DATE>26-FEB-1987 15:01:01.79</DATE>
<TOPICS><D>cocoa</D></TOPICS>
<PLACES><D>el-salvador</D><D>usa</D><D>uruguay</D></PLACES>
<PEOPLE></PEOPLE>
<ORGS></ORGS>
<EXCHANGES></EXCHANGES>
<COMPANIES></COMPANIES>
<UNKNOWN> 
&#5;&#5;&#5;C T
&#22;&#22;&#1;f0704&#31;reute
u f BC-BAHIA-COCOA-REVIEW   02-26 0105</UNKNOWN>
<TEXT>&#2;
<TITLE>BAHIA COCOA REVIEW</TITLE>
<DATELINE>    SALVADOR, Feb 26 - </DATELINE>
<BODY>Showers continued throughout the week in the Bahia cocoa zone, [...] 
Final figures for the period to February 28 are expected to be published 
by the Brazilian Cocoa Trade Commission after carnival which ends midday 
on February 27.
 Reuter
&#3;</BODY></TEXT>
</REUTERS>
```

Looking at a few others gives us the same form.  Awesome!  I can pull out a few things here to make a slightly slimmer, more friendly-for-ES dataset.  We'll need the title and body of each of these.

You might be thinking, "Oh, easy!  Just use [regular expressions on it](https://stackoverflow.com/a/1732454)."  Alas, that would be a _grave error indeed_.  What I'll do is make a short [Beautiful Soup](https://beautiful-soup-4.readthedocs.io/en/latest/) script in Python and scrape it that way.  

```python
import json
from bs4 import BeautifulSoup

# Open the sgm files... for now, just pick one.
reut_sgm_id = "000"
with open(f"reut2-{reut_sgm_id}.sgm", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "lxml")

# Find all the "reuters" tags, which each article has as an outer tag.
soup_reuters_tags = soup.find_all("reuters")

# For each article, get the title and the body.
for idx, soup_reuter_tag in enumerate(soup_reuters_tags):
    title = soup_reuter_tag.find("title")
    title_txt = "" if not title else title.get_text(strip=True)
    content = soup_reuter_tag.get_text(strip=True).replace("\n", " ")
    doc_data = {"title": title_txt, "content": content}

    # Open a json file and pop in the title and body.
    # Each article has its own file.
    with open(
        f"./scraped_documents/doc_{reut_sgm_id}_{idx:0>4}.json", 
        "w+", 
        encoding="utf-8"
    ) as j:
        json.dump(doc_data, j)
```

Not elegant, but gets the job done.  The files each look something like:

```json
{
    "title": "COBANCO INC <CBCO> YEAR NET",
    "content": "26-FEB-1987 15:18:59.34earnusaF f0772reute r f 
[...] or five cts per shr.  Reuter"
}
```

<figure>
    <img src="../assets/images/elasticsearch-tutorial-04_blah.png"
         alt="Blah, Blah">
    <figcaption>Some of these articles are better than others...</figcaption>
</figure>

Which reads weird but _is_ actually in the original data.  The first thousand of these articles ought to be good to practice on, then later I can pop in the rest if I want.

## Dockerized Kibana and Elasticsearch

I'll be using the full [docker compose yaml](https://www.elastic.co/guide/en/elasticsearch/reference/current/docker.html#docker-compose-file) and .env file from ES.  I felt bad not leaving the SSL stuff in during my first part of this post series, so it's back in now.  One `docker compose up` later and I'm ready to go to <localhost:5601> and get started.

Going into the **Search** section, I find **Upload a File**.  I'll do that to make sure my files make sense to ES.

<figure>
    <img src="../assets/images/elasticsearch-tutorial-04_es_1.png"
         alt="ES Home Screen.">
    <figcaption>The home screen.</figcaption>
</figure>

<figure>
    <img src="../assets/images/elasticsearch-tutorial-04_es_2.png"
         alt="ES API Upload.">
    <figcaption>Upload via the API.</figcaption>
</figure>

<figure>
    <img src="../assets/images/elasticsearch-tutorial-04_es_3.png"
         alt="Warning!">
    <figcaption>My file structure cannot be determined... :'[</figcaption>
</figure>

Alas, they do not.  I get a "File Structure Cannot Be Determined" error.  Ugh.  I decide to make my own index ("New Index") and the ingestion type is via an API.  I choose Python for the language.  It tells me to generate an API key, and I do.  I had to update permissions for the API key to allow it to set `verify_certs=False` in my script below:

```python
from elasticsearch import Elasticsearch

# Get API from the Kibana "API Ingestion" page.
API_KEY = "this_was_my_API_key"
ES_ADDRESS = "https://localhost:9200"

es = Elasticsearch(hosts=ES_ADDRESS, api_key=API_KEY, verify_certs=False)

print(es.info())
```

I realized something at this point.  My old script was making files that I would have to re-read and import into this.  Why didn't I just copy-paste this into my previous script and do it all at once?  Why not, indeed.

Here's the whole shebang:

```python
import json
from bs4 import BeautifulSoup
from elasticsearch import Elasticsearch

# Get API from the Kibana "API Ingestion" page.
API_KEY = "this_was_that_cool_API_key_I_had"
ES_ADDRESS = "https://localhost:9200"

es = Elasticsearch(hosts=ES_ADDRESS, api_key=API_KEY, verify_certs=False)

# Open the sgm files... for now, just pick one.
reut_sgm_id = "000"
with open(f"reut2-{reut_sgm_id}.sgm", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "lxml")

# Find all the "reuters" tags, which each article has as an outer tag.
soup_reuters_tags = soup.find_all("reuters")

# For each article, get the title and the body.
# We have to append the index before each article.
operations = []
for idx, soup_reuter_tag in enumerate(soup_reuters_tags):
    title = soup_reuter_tag.find("title")
    title_txt = "" if not title else title.get_text(strip=True)
    content = soup_reuter_tag.get_text(strip=True).replace("\n", " ")

    operations.append({"index": {"_index": "search-reuters"}})
    operations.append({"title": title_txt, "content": content})

es.bulk(operations=operations)
```

As soon as this worked, I looked at the "Documents" section of the index and...

<figure>
    <img src="../assets/images/elasticsearch-tutorial-04_es_4.png"
         alt="All the documents!">
    <figcaption>My documents!</figcaption>
</figure>

Yes!  It worked.  I tried a simple full-text search first before doing anything fancy.

## TODO THINGS

This is a placeholder for me to write the rest of this post.  Make a pipeline, do kNN, and do ELSER!

<!-- ## Next Time

The next thing that the tutorial recommends doing is a [Chatbot Tutorial](https://www.elastic.co/search-labs/tutorials/chatbot-tutorial/welcome).  Since this tutorial goes over the [Langchain](https://www.langchain.com/) project and works with some concepts I'm not familiar with, I think it might be fun to try out.

See you there! -->
