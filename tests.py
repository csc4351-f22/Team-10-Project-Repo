"""
Unit tests for server etc
"""
import unittest
from vader import ave_sent_score, sent_score

class TestVader(unittest.TestCase):
    """_summary_
        Testing class for vader.py functions
    """
    def test_positive_comment(self):
        """Tests result of positive comment in vader
        """
        pos_comment = "I LOVE CATS THEY ARE AMAZING!!!"
        observed = sent_score(pos_comment)
        expected = 0.8713
        self.assertEqual(observed, expected)

    def test_negative_comment(self):
        """Tests result of negative comment in vader
        """
        pos_comment = "kill all humans i hate hate hate them"
        observed = sent_score(pos_comment)
        expected = -0.9501
        self.assertEqual(observed, expected)

    def test_neutral_comment(self):
        """Tests result of neutral comment in vader
        """
        pos_comment = "Pickles"
        observed = sent_score(pos_comment)
        expected = 0.0
        self.assertEqual(observed, expected)

    def test_sentiment_average(self):
        """_summary_
            Tests vader functions
        """
        test_comments = ["Hello my name is Sam.", "i hate pizza", "I love cookies"]
        observed = ave_sent_score(test_comments)
        expected = 0.021666666666666685
        self.assertEqual(observed, expected)

if __name__ == '__main__':
    unittest.main()
