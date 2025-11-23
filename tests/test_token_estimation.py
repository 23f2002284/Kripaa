import sys
import os
# Add the project root to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.token_estimation import count_tokens, estimate_cost, tracker, PRICING

def test_token_estimation():
    print("Testing Token Estimation...")
    
    # 1. Test Token Counting
    text = "This is a test string for token counting."
    count = count_tokens(text)
    expected = len(text) // 4
    print(f"Text length: {len(text)}, Estimated tokens: {count}")
    assert count == expected, f"Token count mismatch: {count} != {expected}"
    
    # 2. Test Cost Estimation
    model = "gemini-2.5-flash"
    input_tokens = 1_000_000
    output_tokens = 1_000_000
    cost = estimate_cost(input_tokens, output_tokens, model)
    expected_cost = PRICING[model]["input"] + PRICING[model]["output"]
    print(f"Cost for 1M in/out on {model}: ${cost}")
    assert abs(cost - expected_cost) < 0.0001, f"Cost mismatch: {cost} != {expected_cost}"
    
    # 3. Test Tracker
    tracker.reset()
    tracker.add_usage(1000, 500, model)
    stats = tracker.get_stats()
    print(f"Tracker Stats: {stats}")
    assert stats.total_input_tokens == 1000
    assert stats.total_output_tokens == 500
    assert stats.total_cost_usd > 0
    
    print("All tests passed!")

if __name__ == "__main__":
    test_token_estimation()
