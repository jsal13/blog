# Using Sklean Pipelines for Fun and Profit

<!-- ID: 202306060010 -->
Last Updated: _2023-06-06_

---

## Introduction

Sklearn's [pipelines](https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html) are an elegant way to organize modeling workflows.  It also provides an "at-a-glance" picture of what is going into the current model &mdash; something your future self will thank you for when you read that notebook back in six months and have no idea what anything is doing.

## Getting Toy Data To Play With

I'll be working with the cute [Penguins](https://github.com/allisonhorst/palmerpenguins) dataset which **seaborn** can load.  The "goal" of my classifier: try to predict the sex of the penguin, given the rest of the features.  **This model will purposely be simplistic: it will serve only to help explain how to set up pipelines.**

## Loading the Data

I made a CSV of the data and a script to load it.  **In this post, I've opted to use [Polars](https://pola.rs/) over [Pandas](https://pandas.pydata.org/docs/index.html).**  

!!! note "Pandas?"

    If you prefer [Pandas](https://pandas.pydata.org/docs/index.html) there should only be changes required for this next code block, but all the code after this code block should work without changes.

```python
import polars as pl
from sklearn.model_selection import train_test_split

df = pl.read_csv("./datasets/penguins.csv", null_values=["NA"], dtypes={"year": str})
df = df.drop_nulls(subset=["sex"])

x = df.drop("sex")
y = df.select((pl.col("sex") == "male").alias("target").cast(int))

# A weird quirk for sklearn.
y = y.to_numpy().ravel()

x_train, x_test, y_train, y_test = train_test_split(
    x, y, test_size=0.33, random_state=1234
)
```

The file contains null values of the form "NA" so I set `null_values=["NA"]` to make Polars understand that those are nulls.  Additionally, Polars will think that a year is an `int` but I want it as a categorical so we set the dtype to be `str`.  Since I'm predicting on **sex**, I'm going to drop any rows that have a null in that column since they won't give me any new predictive information.

I define `x` and `y` in the next few lines.  The `df.select(...)` part is a bit strange if you haven't seen it before, so let me go through it:

1. `pl.col("sex")` picks out the **sex** column,
2. `pl.col("sex") == "male"` compares the column to the string `"male"`, resulting in a column which is either `True` or `False`,
3. `.alias("target")` gives the name **target** to this new boolean column,
4. `.cast(int)` casts the new **target** column as an `int` column (`True` goes to `1`, `False` goes to `0`),
5. `df.select(...)` wraps around the whole thing to say, "I'm working with `df`, and we're going to do something with the columns of this dataframe.`  See [the docs](https://docs.pola.rs/py-polars/html/reference/dataframe/api/polars.DataFrame.select.html) for a bit more detail on this and some examples.

This might seem a bit more complicated compared to the Pandas version, which goes something like `(df["sex"] == "male").astype(int)` but as the number or complexity of derived columns increases I find that Polars is much more readable.

Either way, looking at the next part, what the heck is this?

```python
y = y.to_numpy().ravel()
```

I do this because during the fitting process later, sklearn will require my target values to be a 1D array.  Currently, it is a Polars Series, which, when I make it into a _numpy_ array will become a `(num_rows, 1)` ndarray.  Sklearn requires this be `(num_rows,)` &mdash; that is, a flat array &mdash; which I can get using `.ravel()`.  It's weird but it makes sense if you look at the underlying arrays (pre- and post-ravel). 

Last, I do a train-test split.

```python
x_train, x_test, y_train, y_test = train_test_split(
    x, y, test_size=0.33, random_state=1234
)
```

Nothing wild here.  This gives me two different sets of feature and target sets: one to use for training, one to use for testing.

## Pipelines

A `Pipeline` takes a list of 2-tuples `(name, transform)` where a `transform` in Sklean is anything which has implemented the `fit`/`transform` methods (see [the docs](https://scikit-learn.org/stable/data_transforms.html) for more on this).  The pattern I'll use is roughly like this:

!!! warning "This is Pseudo-code."

```python
# List of columns to transform in this pipeline.
some_column_list = [...]

# List of transformations, in order, to apply.
pipeline = Pipeline(
    [
        ("name_of_transformer_1", Transformer1()),
        ("name_of_transformer_2", Transformer2()),

    ]
)

# Make the transformer, which will apply ALL transformations.
# In this case, there is only the one above.
col_transformer = ColumnTransformer(
    [
        ("col_pipeline", pipeline, some_column_list),
    ]
)

# Fit the transformer with training data.
col_transformer.fit(x_train, y_train)
```

This is the gist of how pipelines work: pick columns to apply the transforms to, make a pipeline to list the transformers to apply, and then apply all the pipelines using the (I think) awkwardly named `ColumnTransformer`.  It's going to look like a lot, but all I'm doing is filling out the above with a few standard transformers.  Right now, you don't need to know what these transformers even _do_, so long as you know they _do something_.

```python
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Make pipelines for specific columns.
cols_numeric = ["bill_length_mm", "bill_depth_mm", "flipper_length_mm", "body_mass_g"]
pipeline_numeric = Pipeline(
    [
        ("impute_w_mean", SimpleImputer(strategy="mean")),
        ("scale_normal", StandardScaler()),
    ]
)

cols_categorical = ["species", "island", "year"]
pipeline_categorical = Pipeline(
    [
        ("impute_w_most_frequent", SimpleImputer(strategy="most_frequent")),
        ("one_hot_encode", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ]
)

# Put it all together into a transformer.
preprocessing_transformer = ColumnTransformer(
    [
        ("numeric", pipeline_numeric, cols_numeric),
        ("categorical", pipeline_categorical, cols_categorical),
    ]
)

# Fit the transformer with training data.
preprocessing_transformer.fit(x_train, y_train)

# ---
print(preprocessing_transformer.get_feature_names_out(), end="\n\n")
print(preprocessing_transformer.fit_transform(x_train, y_train))
```

At the end, I printed the values:

```text
['numeric__bill_length_mm' 'numeric__bill_depth_mm'
 'numeric__flipper_length_mm' 'numeric__body_mass_g'
 'categorical__species_Adelie' 'categorical__species_Chinstrap'
 'categorical__species_Gentoo' 'categorical__island_Biscoe'
 'categorical__island_Dream' 'categorical__island_Torgersen'
 'categorical__year_2007' 'categorical__year_2008'
 'categorical__year_2009']

[[-1.00173392  0.34890155 -1.47813963 ...  1.          0.
   0.        ]
 [ 0.00368887  0.08989674  1.22603896 ...  0.          1.
   0.        ]
 [-0.4716019   1.17771697 -0.26837552 ...  0.          1.
   0.        ]
 ...
 [ 1.53924369  1.48852275  0.22976264 ...  0.          1.
   0.        ]
 [ 0.93599001 -0.47991386  1.9376649  ...  0.          1.
   0.        ]
 [ 0.46069923 -0.27271    -0.69535109 ...  0.          1.
   0.        ]]
```

Great.  The `.fit_transform(...)` has given me the latter array which is ready to be popped into a model.  I'll do just that with a `RandomForestClassifier`, though any classifier would work for my purposes in this post.

```python
from sklearn.ensemble import RandomForestClassifier

# Make a RF Classifier and pipeline it with the preprocessor.
rf_clf = RandomForestClassifier()

preprocess_model_pipeline = Pipeline(
    [("preprocessing", preprocessing_transformer), ("classifier", rf_clf)]
)

preprocess_model_pipeline.fit(x_train, y_train)
y_predicted = preprocess_model_pipeline.predict(x_test)
```

I've created another pipeline which includes the preprocessing (the thing I defined above) and our new classifier.  The raw data is processed first by the `preprocessing_transformer`, then spit out into the `rf_clf` RF Classifier.  One cool thing is that I don't need to keep `.fit`-ing everything, I can call `.fit(...)` on the pipeline and it'll push the data through!  Similarly, I can call `.predict(...)` on the pipeline and it will do what I expect: give me an array of predictions for my test values.

## Scoring the Model

How did the model do?

```python
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

scores = [
    ("accuracy", accuracy_score(y_test, y_predicted)),
    ("precision", precision_score(y_test, y_predicted)),
    ("recall", recall_score(y_test, y_predicted)),
    ("f1", f1_score(y_test, y_predicted)),
]

for score in scores:
    print(score[0], ":", round(score[1],4))
```

```text
accuracy : 0.9
precision : 0.8627
recall : 0.9167
f1 : 0.8889
```

Not _terrible_ for some standard transformers and random forest classification!

## Adding to Pipelines

Besides keeping everything together, pipelines allow the modeler to see what's happening to the data at what stage and easily add new transformers to the flow.  For example, what if I wanted to use some other strategy with our `SimpleImputer`?  What if I wanted to add a second `Scaler` for some reason?  What if I wanted to add a [custom transformer](https://scikit-learn.org/stable/modules/preprocessing.html#custom-transformers)?

This becomes a matter of adding something onto a list.  If you've seen notebooks where transforms are peppered across multiple random cells in a Jupyter notebook (or, worse, in multiple Jupyter Notebooks!), then it's easy to appreciate how nice and clean this makes things.

_Tidy is good.  Be tidy._
