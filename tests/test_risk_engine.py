import unittest

from risk_engine import aggregate_signals, extract_keyword_signals, extract_price_signals


class RiskEngineTests(unittest.TestCase):
    def test_keyword_signal_detects_replica(self):
        signals = extract_keyword_signals("Кроссовки реплика 1:1")
        labels = [s.label for s in signals]
        self.assertTrue(any("реплика" in label for label in labels))

    def test_price_signal_detects_big_discount(self):
        signals = extract_price_signals(current_price=40000, reference_price=120000)
        self.assertTrue(any(s.score_delta > 0 for s in signals))

    def test_aggregate_caps_score(self):
        signals = extract_keyword_signals("реплика копия не оригинал aaa")
        result = aggregate_signals(signals)
        self.assertLessEqual(result.score, 100)


if __name__ == "__main__":
    unittest.main()
