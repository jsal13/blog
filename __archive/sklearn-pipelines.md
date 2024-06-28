# Using Sklean Pipelines for Fun and Profit

<!-- ID: 202306060010 -->
Last Updated: _2023-06-06_

---

## Introduction

Sklearn's [pipelines](https://scikit-learn.org/stable/modules/generated/sklearn.pipeline.Pipeline.html) are an elegant way to organize modeling workflows.  It provides an at-a-glance picture of what happens to what data as it moves through modeling &mdash; something your future self will thank you for when you need to read your notebook again in six months.

I'll be working with the cute [Penguins](https://github.com/allisonhorst/palmerpenguins) dataset which can be loaded through **seaborn**.  The "goal" of my classifier: try to predict the sex of the penguin given the rest of the features.  **This model will purposely be simplistic: its main purpose is to help explain how to set up pipelines.**

## Loading the Data

I make a CSV of the data and a script to load it.  **In this post, I've opted to use [Polars](https://pola.rs/) over [Pandas](https://pandas.pydata.org/docs/index.html).**  

!!! note "Pandas?"

    If you prefer [Pandas](https://pandas.pydata.org/docs/index.html) there should only be changes required for this next code block, but all the code after this code block should work without changes.  [Why change from Pandas to Polars?](https://blog.jetbrains.com/dataspell/2023/08/polars-vs-pandas-what-s-the-difference/#why-use-polars-over-pandas?)

```python
import polars as pl
from seaborn import load_dataset
from sklearn.model_selection import train_test_split


df = pl.from_pandas(load_dataset("penguins"))  # Seaborn does not support to-polars yet.
df = df.drop_nulls(subset=["sex"])  # Predicting on sex, so drop rows that don't include it.

x = df.drop("sex")
y = df.select((pl.col("sex") == "Male").cast(int).alias("target"))

# A weird quirk for sklearn.
y = y.to_numpy().ravel()

x_train, x_test, y_train, y_test = train_test_split(
    x, y, test_size=0.33, random_state=1234
)
```

If you haven't seen polars before, the `df.select(...)` part looks a bit strange.  I'll go through it in more detail:

1. `pl.col("sex")` picks out the **sex** column,
2. `pl.col("sex") == "Male"` compares the column to the string `"Male"`, resulting in a column (actually, a `polars.dataframe.frame.DataFrame` with one column) which is `bool`-type (either `true` or `false`),
3. `.cast(int)` takes the `bool`-type column and casts it as an `int` column (`true` goes to `1`, `false` goes to `0`),
4. `.alias("target")` gives the name **target** to the new `int` column,
5. `df.select(...)` wraps around the whole thing to say, "I'm working with `df`, and we're going to do something with the columns of this dataframe.`  See [the docs](https://docs.pola.rs/py-polars/html/reference/dataframe/api/polars.DataFrame.select.html) for a bit more detail on this and some examples.

The corresponding Pandas version for creating the `target` column, if you're following along that way, goes something like `(df[["sex"]] == "Male").rename(columns={"sex": "target"}).astype(int)`. It's roughly the same as the Polars version but I find the latter more readable as the complexity grows.

Either way, looking at the next line, what the heck is this:

```python
y = y.to_numpy().ravel()
```

Much later in the fitting process, sklearn will require my target values to be a flat 1D array.  Isn't my `target` column already a 1D array if I call `y.to_numpy()` on it?  Surely, this will give me a flat 1D array!  Alas: _No_, it will convert our Polars Series into an `ndarray` of shape `(num_rows, 1)`: this is a 1D array which looks roughly like `[[1], [0], [1], [1], ...]` and sklearn requires it to look like `[1, 0, 1, 1, ...]`.  Using `.ravel()` on the former series gives me the latter series and sklearn will be happy.  Since this isn't a post on what sklearn does and doesn't like, don't worry if this seems weird &mdash; because it is weird.

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

In Python, this looks something like:

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

cols_categorical = ["species", "island"]
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

Take a second to look over this and piece together what's happening.  I'm applying different transformations to my numeric columns (`cols_numeric`) than my categorical columns (`cols_categorical`) and we can see which columns go with which transforms by looking at the `ColumnTransformer` input.  Calling `.fit` on the `ColumnTransformer` will apply each pipeline to its respective columns.

At the end of this script, I printed the values so I can see what I get:

```text
['numeric__bill_length_mm' 'numeric__bill_depth_mm'
 'numeric__flipper_length_mm' 'numeric__body_mass_g'
 'categorical__species_Adelie' 'categorical__species_Chinstrap'
 'categorical__species_Gentoo' 'categorical__island_Biscoe'
 'categorical__island_Dream' 'categorical__island_Torgersen'
]

[[-1.00173392  0.34890155 -1.47813963 ...  1.          0.
   1.        ]
 [ 0.00368887  0.08989674  1.22603896 ...  0.          1.
   1.        ]
 [-0.4716019   1.17771697 -0.26837552 ...  0.          1.
   1.        ]
 ...
 [ 1.53924369  1.48852275  0.22976264 ...  0.          1.
   1.        ]
 [ 0.93599001 -0.47991386  1.9376649  ...  0.          1.
   1.        ]
 [ 0.46069923 -0.27271    -0.69535109 ...  0.          1.
   1.        ]]
```

Great.  The `.fit_transform(...)` gives me an array that I can pop into a model.  I'll do that with a `RandomForestClassifier`, though any classifier would work for my purposes in this post:

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

I've created another pipeline which includes the preprocessing and our new classifier.  The raw data is processed first by the `preprocessing_transformer`, then spit out into the `rf_clf` RF Classifier.  Notice that I can call `.fit` and `.predict` as a methods from the _pipeline_ object and it will automatically do all the pipeline fitting and model predicting.

## Adding to Pipelines

Besides keeping everything nice, tidy, and together, pipelines allow the modeler to see what's happening to the data at what stage and easily add new transformers to the flow.  For example, what if I wanted to use some other strategy with our `SimpleImputer`?  What if I wanted to add a second `Scaler` for some reason?  What if I wanted to add a [custom transformer](https://scikit-learn.org/stable/modules/preprocessing.html#custom-transformers)?

This becomes a matter of adding something onto a list.  If you've seen notebooks where transforms are peppered across multiple random cells in a Jupyter notebook (or, worse, in multiple Jupyter Notebooks!), then it's easy to appreciate how nice and clean this makes things.  Try pipelining out!

_Tidy is good.  Be tidy._
