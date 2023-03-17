"""_summary_
File defining functions for use of Vader sentiment analysis model
"""
import ssl
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# from nltk import tokenize
import nltk


def setup_vader():
    #pylint: disable=protected-access
    """_summary_
    Trying to get linter to behave with protected
    member issue with ssl calls.
    """
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context
    nltk.download("vader_lexicon")

setup_vader()

# this function takes in a list of comments and outputs a corresponding
# list of sentiment scores ranging from -1 to 1
def sent_score(comment):
    """_summary_
    Calculate sentiment score on a single comment using Vader
    Args:
        comment (_type_): _description_

    Returns: Sentiment score
        _type_: float
    """
    # initalize an empty array for the scores
    score = 0

    # initalize the model
    sid = SentimentIntensityAnalyzer()
    # a dictionary s
    polar_scores = sid.polarity_scores(comment)

    for key, value in polar_scores.items():
        if key == "compound":
            score = value

    # OPTIONAL could use to return a tuple of the comments
    # and the sentiment score to be put
    # into a database
    # comsAndScores = {}
    # for key in comments:
    #    for value in score:
    #        comsAndScores[key] = value
    #        score.remove(value)
    #        break
    # print(score)
    return score


def ave_sent_score(comments):
    """_summary_
    Calculate average sent score for a list of comments
    Args:
        comments (list): list of aggregated comments (from a video)

    #example list of comments:
    #comments = ["Hello my name is Sam.", "i hate pizza", "I love cookies"]
    """
    total = 0
    for comment in comments:
        total = total + sent_score(comment)
    return total / len(comments)
