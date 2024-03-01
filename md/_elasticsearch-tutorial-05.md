# The Elasticsearch Tutorial: Part 5, Chatbot Example

<!-- ID: 0050 -->
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




<!-- ## Next Time

The next thing that the tutorial recommends doing is a [Chatbot Tutorial](https://www.elastic.co/search-labs/tutorials/chatbot-tutorial/welcome).  Since this tutorial goes over the [Langchain](https://www.langchain.com/) project and works with some concepts I'm not familiar with, I think it might be fun to try out.

See you there! -->
