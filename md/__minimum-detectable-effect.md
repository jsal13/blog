# The Elasticsearch Tutorial: Part 1, Full Search

<!-- ID: 202404050010 -->
Last Updated: _2024-04-05_

---

I was recently in an interview and the interviewer asked me: 

"Pretend I'm a data science intern.  Explain what a _Minimal Detectable Effect_ (MDE) is."

I remembered the term from teaching business statistics many years ago, but I hadn't seen it in a while.  Something to do with power calculations?  Something to do with the size of a sample?  _Something_ like that.  I had to say I didn't remember what it was and I swear the interviewer did a _tsk_.

Might have been my imagination.

To remedy this hole in my understanding, and because this concept does come up in A/B testing, I decided to learn-by-teaching it here.

## 0.5 Percent Better

A few years ago I was at a company and tasked with making some dashboards for our A/B tests.  One of the tests, which I'll refer to as _Purple Page_ test, completely changed the payment page for the user (think: paying off a credit card online) from a basic "no nonsense" big letter white-and-black to a page with a purple background and much smaller, harder-to-read (even for me) white letters.  It looked more modern and hip for sure &mdash; but our users were almost certainly going to skew older.  Additionally, this was a massive change: typically changes were small and incremental (as is often suggested in A/B testing).  Given all this, there were lengthy discussion over the page but ultimately, because the designer of the purple page was _also_ the Marketing VP &mdash; and because this was a small company where most of the power was at the top &mdash; the execs said, "We'll do an A/B test and see who wins."

I don't remember the details but, at the end of a one month test, there were enough users for me to feel relatively confident that we could end the experiment.  The results?  The purple page had more conversions &mdash; by 0.5%.  That is, if there were 1,000 conversions for the white page, there were 1,005 for the purple page.

As you might expect, given that I'm telling this story in a "Minimum Detectable Effect" post, the purple page was declared the winner and the _Purple Test_ was complete.  It doesn't matter if I _did_ include a MDE calculation (I did) or if the VP cared about it at all (he didn't), but it brings us to the main question this post is going to try to answer:

**If the white page had 1,000 conversions, how many conversions would the purple page need to "win"?**

## What is Winning, Who is Best

This is where things get sticky.  What would it mean for one thing to be an improvement over another thing?

**The conversion rate of a task is the percentage of users who have completed a desirable action.**  For example, those who sign up for a newsletter, those who click a certain button, those who type in their name in the right field, etc.  If 50 of my 1,000 pageviews click a donation button, that's a conversion rate of (50 / 1,000 = ) 0.05, or 5%, for the task of "clicking a donation button" for the population of users visiting my page.

If I made my donation button black-and-white for 50% of my page viewers and purple-and-white for the other 50%, I could compare the conversion rates of those who click the donate button by dividing the values; if 5% clicked on the black-and-white but 9% clicked on the purple-and-white, that's an improvement of (0.09 / 0.05 = 1.8, so) 80%.  Said another way, if 1,000 people went to each option we would have 50 people clicking on the black-and-white version and 90 clicking on the purple-and-white version which is, again an (90 / 50 = 1.8) 80% improvement.

!!! warning "Warning"

  The paragraph above assumes the conversion rates are calculated using N, the number of people, large enough to give confidence that the conversion rate is "close enough" to the true conversion rate.  The issue would be if, for example, one conversion rate was calculated with 10,000 people and another was calculated with 10 people: the latter "conversion rate" probably isn't very close to the true conversion rate for that activity.


