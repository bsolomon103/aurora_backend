def check_start_assessment(text):
    target_phrase = 'start assessment'
    threshold = 0.8  # Adjust the threshold as needed

    # Remove whitespace and convert the input text to lowercase
    processed_text = text.strip().lower()

    # Calculate the Levenshtein distance between the target phrase and each substring
    for i in range(len(processed_text)):
        for j in range(i + 1, len(processed_text) + 1):
            substring = processed_text[i:j]
            distance = levenshtein_distance(target_phrase, substring)
            similarity = 1 - (distance / max(len(target_phrase), len(substring)))
            
            # Check if the similarity exceeds the threshold
            if similarity >= threshold:
                return True

    return False


def levenshtein_distance(s, t):
    m, n = len(s), len(t)
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = 0 if s[i - 1] == t[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)

    return dp[m][n]
