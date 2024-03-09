# Refactoring: Code with Business Logic

<!-- ID: 202311010010 -->
Last Updated: _2023-11-01_

---

Refactoring can be difficult and time-consuming, but it is _absolutely necessary_ if one wants to maintain a clean codebase and have code which is easy to read, extend, scale, and share.

I'll show an example of how I would refactor a specific small project. _Note that this may not be how everyone refactors and I may make some choices which others may have done differently_.  In my refactors, for example, I tend to favor what I consider to be "Pythonic" readability over minor optimizations.

I'll work in Python for this post but all of these issues can and do pop up in every other language and are solved in similar ways.

## The Problem and First Solution

**Problem**: The job of the following code is to make a (string) label for another module when it is called.  For example, it may return "Minor: Prime (New Customer)" which implies the customer is under 18 years old, has Prime FICO rating (don't worry if you don't know what this is!), and is a new customer.

```python
# ORIGINAL, NO REFACTORING.

# customer_type.py

def main(a, b, c, d, e):
    # a: first name
    # b: last name
    # c: age
    # d: fico score
    # e: previous customer???
    if c < 18:
        if d < 580:
            if e == True:
                return "Minor: Deep Subprime (Previous Customer)"
            if e == False:
                return "Minor: Deep Subprime (New Customer)"
        if d > 580 and d <= 620:
            if e == True:
                return "Minor: Subprime (Previous Customer)"
            if e == False:
                return "Minor: Subprime (New Customer)"
        if d > 619 and d <= 620:
            if e == True:
                return "Minor: Near Prime (Previous Customer)"
            if e == False:
                return "Minor: Near Prime (New Customer)"
        if d > 660 and d <= 719:
            if e == True:
                return "Minor: Prime (Previous Customer)"
            if e == False:
                return "Minor: Prime (New Customer)"
        if d >= 720:
            if e == True:
                return "Minor: Super-Prime (Previous Customer)"
            if e == False:
                return "Minor: Super-Prime (New Customer)"
    else:
        if d < 580:
            if e == True:
                return "Adult: Deep Subprime (Previous Customer)"
            if e == False:
                return "Adult: Deep Subprime (New Customer)"
        if d > 580 and d <= 620:
            if e == True:
                return "Adult: Subprime (Previous Customer)"
            if e == False:
                return "Adult: Subprime (New Customer)"
        if d > 619 and d <= 620:
            if e == True:
                return "Adult: Near Prime (Previous Customer)"
            if e == False:
                return "Adult: Near Prime (New Customer)"
        if d > 660 and d <= 719:
            if e == True:
                return "Adult: Prime (Previous Customer)"
            if e == False:
                return "Adult: Prime (New Customer)"
        if d >= 720:
            if e == True:
                return "Adult: Super-Prime (Previous Customer)"
            if e == False:
                return "Adult: Super-Prime (New Customer)"
```

It may be surprising (or not) to know that this is (strongly) based on a real function I inherited while at a past job.  At least they gave us some comments on what the arguments mean!

There's a lot to pick through, so I'm going to list some things which aren't great:

- Non-descriptive variable names and Unused Variables,
- Repetition of similar code,
- Functions / Classes which are doing many things at once,
- "Magic Numbers" (numbers which are seemingly random in the code),
- No Type Hinting (very common in Python code, as type hinting is optional),
- No Docstrings / Documentation.

Reading through the code, I get the gist of what's going on: lots of `if`-statements which eventually spit some label out.  Ask yourself: what would have to be done here if a new range of score was added?  What if I had a new age group (say, "> 65")?  How much more frustrating would this code be to read through?

## Non-Descriptive Variable Names and Unused Variables

There are few (if any) reasons these days not to make a variable name expressive. In the past, due to space limitations, variables might look like `CLS21` and have a data dictionary which noted what meant what.  Today, I can expand them out to make them more clear.

Additionally, let's take out any variables/arguments which are not being used by the code.  There may be reasons to keep these variables in (for example, to make a connection work with an existing API) but I will assume they are unnecessary in this case.

```python
# FIRST REFACTOR: Descriptive Variable Names, No Unused Variables.

# customer_type.py

def main(age, fico_score, is_previous_customer):
    if age < 18:
        if fico_score < 580:
            if is_previous_customer == True:
                return "Minor: Deep Subprime (Previous Customer)"
            if is_previous_customer == False:
                return "Minor: Deep Subprime (New Customer)"
...
...
```

At this point, I can remove the "docs" at the top since the variables are expressive.  I'll put a proper docstring in later.

## Repetition, Don't Repeat Yourself (DRY)

One important principle to consider when refactoring is _DRY: Don't Repeat Yourself_.  When you have virtually identical code that appears two or more times, you may want to consider making this code into its own variable, function, or class.  One main reason for this is: if you need to change or debug the code, then you only need to change or debug it in one place instead of however many times you've copy-pasted it.  Much easier, much less error-prone.

There are three obvious places to do this in the code above: the `if`-statement that checks for previous customer or new customer, the `if`-statement which checks for "Minor / Adult" and the `if`-statement that checks the score.

In order to refactor these statements, it may be better to make a "template string" which is filled in with some variables as the `if`-statements are worked through.  For example, I start with the blank string, then add in if the customer is a Minor, then add in the Credit Rating, then add in New Customer or not.

```python
# SECOND REFACTOR: TEMPLATE STRINGS + UNNESTING IFs

# customer_type.py

def main(age, fico_score, is_previous_customer):

    customer_age_label = ""
    credit_rating = ""
    prev_or_new_cust =""

    if age < 18:
        customer_age_label = "Minor"
    else:
        customer_age_label = "Adult"

    if is_previous_customer == True:
        prev_or_new_cust = "Previous Customer"
    else:
        prev_or_new_cust = "New Customer"

    if fico_score < 580:
        credit_rating = "Deep-Subprime"
    if fico_score > 580 and fico_score <= 620:
        credit_rating = "Subprime"
    if fico_score > 619 and fico_score <= 620:
        credit_rating = "Near-Prime"
    if fico_score > 660 and fico_score <= 719:
        credit_rating = "Prime"
    if fico_score >= 720:
        credit_rating = "Super Prime"

    customer_label = "{customer_age_label}: {credit_rating} ({prev_or_new_cust})".format(**{
        'customer_age_label': customer_age_label,
        'credit_rating': credit_rating,
        'prev_or_new_cust': prev_or_new_cust
    })

    return customer_label
```

While not _perfect_, it's certainly cleaner and shorter.  There is one Python-specific thing we've done, which is the "[string format() method](https://docs.python.org/3/tutorial/inputoutput.html#the-string-format-method)" at the bottom.  This formatting allows us to easily create strings and use a dictionary to fill things in (notice the `**` which unpacks the dictionary in the `.format` method).  If you don't use Python, or don't want to use string formatting like this, it's also easy to add these variables together in an appropriate way once I have them.

## Functions Doing More Than One Thing

**This function is doing quite a bit.**  It's checking credit rating, if someone is a minor or not, if they're a new or returning customer.  If I was given a ton of business logic, this might become much larger and more difficult to debug.  Let's break this up into smaller functions.  While I'm at it, let's also _put in [type hints](https://docs.python.org/3/library/typing.html)_,

```python
# THIRD REFACTOR: FUNCTIONS SHOULD DO ONE THING.
# customer_type.py

def customer_age_label(age: int) -> str:
    return "Minor" if age < 18 else "Adult"

def credit_rating_label(fico_score: int) -> str:
    if fico_score < 580:
        return "Deep-Subprime"
    if fico_score > 580 and fico_score <= 620:
        return "Subprime"
    if fico_score > 619 and fico_score <= 620:
        return "Near-Prime"
    if fico_score > 660 and fico_score <= 719:
        return "Prime"
    if fico_score >= 720:
        return "Super Prime"

def previous_customer_label(is_previous_customer: bool) -> str:
    return "Previous Customer" if is_previous_customer else "New Customer"

def main(age: str, fico_score: str, is_previous_customer: str) -> str:

    minor_or_adult = customer_age_label(age)
    credit_rating = credit_rating_label(fico_score)
    prev_or_new_cust = previous_customer_label(is_previous_customer)

    customer_label = "{minor_or_adult}: {credit_rating} ({prev_or_new_cust})".format(**{
        'minor_or_adult': minor_or_adult,
        'credit_rating': credit_rating,
        'prev_or_new_cust': prev_or_new_cust
    })

    return customer_label
```

In Python, type hints are not required (nor are they checked unless you have [mypy](http://mypy-lang.org/), which I recommend using), but it is important to get into the habit of giving type hints (or, for some other languages, using types when auto-types aren't obvious).  This allows us to see, at a glance, which functions are returning what types of things.

## Magic Numbers

**[Magic Numbers](https://en.wikipedia.org/wiki/Magic_number_(programming))** are numbers in code which are meaningful but perhaps not obviously so.  These often should be replaced with constants with a meaningful name which tells us what the magic number means.

In this code, I have the FICO score bounds. Luckily, these are bins and I can do a standard bin structure with an `for`-loop, but there are many other equally nice ways to do this construction.  Here's one:

```python
# FOURTH REFACTOR: NO MAGIC NUMBERS.

# customer_type.py
FICO_UPPER_BOUNDS = {
    "Deep-Subprime": 579,
    "Subprime": 619,
    "Near-Prime": 659,
    "Prime": 719,
    "Super-Prime": 850
}

MINOR_AGE_UPPER_BOUND = 18

def customer_age_label(age: int) -> str:
    return "Minor" if age < MINOR_AGE_UPPER_BOUND else "Adult"

def credit_rating_label(fico_score: int) -> str:
    for lbl, upper_bound in FICO_UPPER_BOUNDS.items():
        if fico_score < int(upper_bound):
            return lbl

def previous_customer_label(is_previous_customer: bool) -> str:
    return "Previous Customer" if is_previous_customer else "New Customer"

def main(age: int, fico_score: int, is_previous_customer: bool) -> str:

    minor_or_adult = customer_age_label(age)
    credit_rating = credit_rating_label(fico_score)
    prev_or_new_cust = previous_customer_label(is_previous_customer)

    customer_label = "{minor_or_adult}: {credit_rating} ({prev_or_new_cust})".format(**{
        'minor_or_adult': minor_or_adult,
        'credit_rating': credit_rating,
        'prev_or_new_cust': prev_or_new_cust
    })

    return customer_label
```

I'm being a bit sloppy here with an early return in the `for`-loop, but we'll fix this soon.  In particular, **mypy** won't be happy with that early return, as it's possible the function could return `None`.

**Reader**: Did you notice that there was a typo in the code, which would cause a null return if someone had a credit score of, say, 630?  Refactoring this code fixed that issue and made it significantly easier to extend, change, or check bounds.

## More Refactoring?

### TODO: IS THIS NECESSARY?
### TODO: PROOFREAD STOP HERE.

Some people would stop at this point &mdash; and, unfortunately, many would have stopped way before this point.

When I made the smaller functions I made one big function (``main``) pass parameters into smaller functions as arguments. Since these smaller functions exist only to help ``main``, an I'm probably not going to be using this function elsewhere, this feels like a code-smell.  Indeed, this code smell could mean that I should introduce a class-type structure in our code.  Let's add this to the list, and then take a crack at some of these other bullet-point issues.  Let's try to do this one first:

Make a Class and Encapsulate

For some Python students, this may be the scariest step.  It's difficult to say when something ought to be a class as opposed to a function; indeed, many times it leads to some fairly heated arguments!  Nevertheless, in this case I will do it to explain how to do it.  (Note: I would favor a class in this case because of the number of parameters I'm passing as arguments to smaller business-logic-type functions.)

```python
# FIFTH REFACTOR: CLASS.

# customer_type.py
FICO_UPPER_BOUNDS = {
    "Deep-Subprime": 579,
    "Subprime": 619,
    "Near-Prime": 659,
    "Prime": 719,
    "Super-Prime": 850
}

MINOR_AGE_UPPER_BOUND = 18

class CustomerLabel:

    def __init__(self, age: int, fico_score: int, is_previous_customer: bool):
        self.age = age
        self.fico_score = fico_score
        self.is_previous_customer = is_previous_customer

        self.customer_label = self.create_customer_label()

    def customer_age_label(self) -> str:
         return "Minor" if self.age < MINOR_AGE_UPPER_BOUND else "Adult"

    def credit_rating_label(self) -> str:
        for lbl, upper_bound in FICO_UPPER_BOUNDS.items():
            if self.fico_score < int(upper_bound):
                return lbl

        # TODO: Put a LOG here to make it known that a label was not returned correctly!
        return ""

    def previous_customer_label(self) -> str:
        return "Previous Customer" if self.is_previous_customer else "New Customer"

    def create_customer_label(self) -> str:
        return f"{self.customer_age_label()}: {self.credit_rating_label()} ({self.previous_customer_label()})"

# Usage:
customer_label = CustomerLabel(age=17, fico_score=550, is_previous_customer=False).customer_label
```

Notice that I've put a structure around this code which makes it trivial to add additional things to the label if I need to.  It also allows us to change the format of the label if that is required.  It is robust, scalable to new business logic, and easy to read through.  There is that weird "usage" thing at the bottom, though...

## Docstrings & Misc

I'm going to add docstrings at this point, since I'm fairly satisfied with the structure of the code.  There are a few tools which allows your editor to generate templates for these docstrings for you, giving you no excuse to not write them!  There are many different ways to write docstrings, so be consistent in your codebase.  If you use something like Sphinx or Swagger, make sure you conform to the required docstring formats.  I will use [Numpy style docstrings](https://numpydoc.readthedocs.io/en/latest/format.html) in this sample.

We've also done some minor cleanup, as noted at the top.  These are minute things which I thought might be nice as I went through the code one last time.  Additionally, we've used [Black](https://github.com/psf/black) to format the code and make it look nice.

```python
"""CustomerLabel class."""

from typing import Dict

FICO_UPPER_BOUNDS: Dict[str, int] = {
    "Deep-Subprime": 579,
    "Subprime": 619,
    "Near-Prime": 659,
    "Prime": 719,
    "Super-Prime": 850,
}

MINOR_AGE_UPPER_BOUND: int = 18


class CustomerLabel:
    """
    Create a customer label.

    The customer label format is: 'Adult/Minor Credit_Rating New/Returning_Customer'

    Methods
    -------
    get_customer_label()
         Return the formatted label.

    Example
    -------
    >>> customer_label = CustomerLabel(
    ...     age=17,
    ...     fico_score=550,
    ...     is_previous_customer=False
    ... ).get_customer_label()

    """

    def __init__(self, age: int, fico_score: int, is_previous_customer: bool):
        """
        Create a customer label.

        Attributes
        ----------
        age : int
            Age of the customer in years
        fico_score : int
            FICO score of the customer
        is_previous_customer : bool
            If the customer is a previous customer or not
        """
        self.age = age
        self.fico_score = fico_score
        self.is_previous_customer = is_previous_customer

    def _customer_age_label(self) -> str:
        """Calculate the customer's age label."""
        return "Minor" if self.age < MINOR_AGE_UPPER_BOUND else "Adult"

    def _credit_rating_label(self) -> str:
        """Calculate the label for credit rating given the FICO bounds."""
        for lbl, upper_bound in FICO_UPPER_BOUNDS.items():
            if self.fico_score < int(upper_bound):
                return lbl

        # TODO: Put a LOG here to make it known that a label was not returned correctly!
        return ""

    def _previous_customer_label(self) -> str:
        """Return corresponding label for previous customer."""
        return "Previous Customer" if self.is_previous_customer else "New Customer"

    def get_customer_label(self) -> str:
        """Generate and returns a customer label."""
        return (
            f"{self._customer_age_label()}: "
            f"{self._credit_rating_label()} ({self._previous_customer_label()})"
        )
```

## Are I Done?

The code looks clean, has docstrings and an example, and doesn't have any obvious code smells.  There is a TODO that I left, which should be converted to a ticket so that I don't forget about it — but, at least, I ought to note it in the code.  Most text editors will be able to show you the "TODO" items you have in your code and it's good to go over these every so often.

Are I done?  I'm sure some of you think that something is still amiss, that something could be done better, that something could be changed — for example, why have a function which converts our bool to an age label when I can do the conversion quickly and easily on one line in our ``__init__``?  There are several other optimizations which could be argued for.

Would you have refactored things differently?  Will our refactor (or your refactor) still be useable if our boss tells us to change the label, add in new arguments, or create different calculations for labels?  Would it be easy for someone new to look at the code and understand what it does?  Would it be easy for someone to look at the code if they were making something which used it as an input or an output?

## Conclusion

My personal feeling is that refactoring is important enough to get a dedicated day during a sprint; it not only will reduce technical debt, get new users familiar with the code, and clean things up, but it will make the code readable and usable for years to come.

There may be those who resist refactoring, call it a waste of time, or tell you that they write perfect code the first time.  **Read through their code and decide for yourself.**
