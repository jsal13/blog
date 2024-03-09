# The Elasticsearch Tutorial: Part 5, Chatbot Example

<!-- ID: 202402240050 -->
Last Updated: _2024-02-29_

---

These will be a continuation of notes from doing the [elasticsearch tutorial](https://www.elastic.co/search-labs/tutorials/search-tutorial/welcome).  This will be written as I go so that you can go on this `journey` with me.

This time I'll be going through the [chatbot tutorial](https://www.elastic.co/search-labs/tutorials/chatbot-tutorial/chatbot-rag-app/setup).

## Preperation

The first few pages of the chatbot tutorial tells me to download the repo (`git clone https://github.com/elastic/elasticsearch-labs`), make a virtual env for python, (`python3 -m venv .venv; source .venv/bin/activate;`) and install the packages (`pip install -r requirements.txt`).  Nothing wild so far!

**A mini-adventure**: I was at Starbucks before a class when I was cloning the repo and the wifi there isn't great.  It refused to download beyond 1%.  I tried to use the `--depth=1` [flag](https://github.blog/2020-12-21-get-up-to-speed-with-partial-clone-and-shallow-clone/) and after 4% I got a different error message:

```shell
error: RPC failed; curl 16 Error in the HTTP2 framing layer
error: 8103 bytes of body are still expected
fetch-pack: unexpected disconnect while reading sideband packet
fatal: early EOF
fatal: fetch-pack: invalid index-pack output
```

Huh.  That's a new one.  I found [this answer](https://github.com/orgs/community/discussions/48568#discussioncomment-5108608) and decided to reset my wifi connection.  Nothing.  I decided to turn the wifi off and on again.  Nothing.  I decided to restart my laptop and &mdash; something!  The download sped to 81% and... failure.  One more time.  It looked like it got to 100% but gave me an error:

<figure>
    <img src="../assets/images/elasticsearch-tutorial-05_gitclone.png"
         alt="So close.">
    <figcaption>Oh come on!</figcaption>
</figure>

As I was writing up this part of the blog I tried one last time and finally &mdash; finally! &mdash it finished and I had a shallow clone of the repo!  That ends that mini-advnture.  Surely, installing the Python packages will go smoother &mdash;

It did.  Whew.  I copy the `.env.example` to `.env` start my docker compose ES clusters.  Luckily, I had already downloaded these before I came to the coffee shop since otherwise there's no way that would `docker pull` in less than an hour and I'd have to give up until I went home.

<!-- The next part has me downloading an LLM, which I _don't_ have locally.  I'll have to download this when I get home.  In the meantime, let me look at what the example app in this repo does. -->

## The Example App

Looking at in the app folder we have an `api`, `data`, and `frontend` folder, and I'll look at those in a minute.  Otherwise, we have some config files and a dockerfile that looks like it runs the flask application.  

In the `frontend` folder we have some things I'm half-familiar with.  I'm familiar with typescript and the Vue framework, but I'm not as familiar with React. Given my limited knowledge, I scanned through the code and found it was mostly things to make the search app look and feel nice.  It's possible we could get the same information with API calls, which tells me that I don't need to spend too much time investigating every piece of this frontend.  I'll move on.

The `data` folder is, surprise, data.  There is also a python script.  The `main()` function of this looks like this:

```python
install_elser()

print(f"Loading data from ${FILE}")

metadata_keys = ["name", "summary", "url", "category", "updated_at"]
workplace_docs = []
with open(FILE, "rt") as f:
    for doc in json.loads(f.read()):
        workplace_docs.append(
            Document(
                page_content=doc["content"],
                metadata={k: doc.get(k) for k in metadata_keys},
            )
        )

print(f"Loaded {len(workplace_docs)} documents")

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=512, chunk_overlap=256
)

docs = text_splitter.transform_documents(workplace_docs)

print(f"Split {len(workplace_docs)} documents into {len(docs)} chunks")

print(
    f"Creating Elasticsearch sparse vector store in Elastic Cloud: {ELASTIC_CLOUD_ID}"
)

elasticsearch_client.indices.delete(index=INDEX, ignore_unavailable=True)

ElasticsearchStore.from_documents(
    docs,
    es_connection=elasticsearch_client,
    index_name=INDEX,
    strategy=ElasticsearchStore.SparseVectorRetrievalStrategy(model_id=ELSER_MODEL),
    bulk_kwargs={
        "request_timeout": 60,
    },
)
```

From the top we see that it tries to install ELSER (which I encountered a few posts ago!), defines some metadata keys, opens up some of the data files and appends the contents there.  The `Document` is from langchain: `langchain.docstore.document` and I'm not sure right now what it does, but it seems like a class to hold the contents of a document.

Parenthetically, I've never seen `"rt"` as an option in `open`, but it turns out that it refers to opening a file in "text" mode, which is the default, so it's the same as `"r"`.

Next, I see `from_tiktoken_encoder` and I'm like, "Wait, TikTok what now?"  From the [langchain documentation on tiktoken](https://python.langchain.com/docs/modules/data_connection/document_transformers/split_by_token):

> Language models have a token limit. You should not exceed the token limit. When you split your text into chunks it is therefore a good idea to count the number of tokens. There are many tokenizers. When you count tokens in your text you should use the same tokenizer as used in the language model.

> tiktoken is a fast BPE tokenizer created by OpenAI.

> We can use it to estimate tokens used. It will probably be more accurate for the OpenAI models.

Okay, so it's not going to tiktok, that's good to know.  I'm chunking up documents and, indeed, the next print statement says exactly that.

The ES Sparse Vector storage is then created, and I will have to fiddle with that so we can have something local to store them if possible.  Next, the code creates an index from our documents.

In the `api` folder I see a few important files.  `llm_integrations.py` connects to openai, or the various other chat AI providers (vertex, azure, etc.), and all of the inits look reasonable and approximately the same.  The `elasticsearch_client.py` is appropriately named: it passes our ES client into `ElasticsearchChatMessageHistory` which, according to the [langchain docs](https://python.langchain.com/docs/integrations/memory/elasticsearch_chat_message_history#initialize-elasticsearch-client-and-chat-message-history) is the way langchain is able to read chat history with ES.  

Two files left: `chat.py` and `app.py`.  The `chat.py` file, which I'll probably look at a bit harder later because it seems like it's doing some heavy lifting to convert the question from the user into something usable, but the tl;dr of the file is, "Takes questions, splits out answers."  

The `api.py` file has two endpoints: `/` which sends us to the index page, and `/app/chat/` which takes the question and returns the response that `elasticsearch_client.py` needs.  There's also a cli command to create or recreate the ES index.

That's all of the sample app stuff.  As I parse through what is happening I'll most likely need to revisit some of these files later, but it's nice to know they exist and it's nice to know where things are.

## Python Back End

Running `flask create-index` gives me an error.

```shell
elastic_transport.TlsError: TLS error caused by: TlsError(TLS error caused by: SSLError([SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:1007)))
```

I've learned from doing this a few times that there's something afoot in the ES client in the Python code and, not wanting to _solve_ this problem so much as _avoid dealing with it_, I added the following to the **/data/index_data.py** file:

```python
if ELASTICSEARCH_URL:
    print(ELASTICSEARCH_URL)
    elasticsearch_client = Elasticsearch(
        hosts=[ELASTICSEARCH_URL], basic_auth=("elastic", "example"), verify_certs=False  # Added this!
    )
```

This'll definitely work, right?  Let's see!

```shell
raise HTTP_EXCEPTIONS.get(meta.status, ApiError)(
elasticsearch.NotFoundError: NotFoundError(404, 'resource_not_found_exception', 'No known trained model with model_id [.elser_model_2]')
```

At _least_ I know where this is!  It's in the same file, in the `install_elser()` function.  I look a bit further down and see...

```shell
raise HTTP_EXCEPTIONS.get(meta.status, ApiError)(
elasticsearch.BadRequestError: BadRequestError(400, 'action_request_validation_exception', "Validation Failed: 1: [model_type] must be set if [definition] is not defined.;2: [inference_config] must not be null.;3: Invalid model_id; '.elser_model_2' can contain lowercase alphanumeric (a-z and 0-9), hyphens or underscores; must start and end with alphanumeric;")
```

Oh, well, sure.  That makes sense.  While looking this up, I see that I need a certain **subscription type** to use ELSER, which makes me a little nervous.  It does not explicitly say this in the requirements but I've been burned before.

I run into a snag here.  I can't figure out what model id I should be using, and doing a `get` for the model ids only gives me a single id for an unrelated model.  I'm worried that I _do_ need a subscription.

TODO: I gott'a figure this out!




<!-- 
## Next Time

The next thing that the tutorial recommends doing is a [Chatbot Tutorial](https://www.elastic.co/search-labs/tutorials/chatbot-tutorial/welcome).  Since this tutorial goes over the [Langchain](https://www.langchain.com/) project and works with some concepts I'm not familiar with, I think it might be fun to try out.

See you there! -->
