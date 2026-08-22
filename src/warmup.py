import math
def moving_average(data, window_size):
    result = []
    if window_size <= 0:
        raise ValueError("window must be > 0")
    if len(data) < window_size:
        raise ValueError("not enough data points")
    
    total_windows = len(data) - window_size + 1
    
    for i in range(total_windows):
        window = data[i:i+window_size]
        avg = sum(window)/window_size
        result.append(round(avg, 2))
    
    return result

    # ---- test the function-------------
    
prices = [100.0, 102.5, 101.0, 105.0, 107.5, 106.0, 110.0]
window = 3
result = moving_average(prices, window)
    
print(f"orgininal data: {prices}")
print(f"3-period moving average: {result}")
print(f"========================================================")
print(f"========================================================")




import math
def standardize(data):
    n = len(data)
    mean = sum(data)/n
    squared_sum = sum((x - mean) ** 2 for x in data)
    sample_variance = squared_sum/(n-1)
    sample_std = math.sqrt(sample_variance)
    if sample_std == 0:
        raise ValueError("std is 0")
    
    standardize_value = [round((x - mean)/sample_std, 2) for x in data]
    return standardize_value


# ------------------ Test the function ---------------------------

raw_data = [10.0, 12.0, 23.0, 16.0, 23.0, 21.0, 16.0]
z_scores = standardize(raw_data)

print(f"orginal Data: {raw_data}")
print("Z-scores:", z_scores)

    
print(f"========================================================")
print(f"========================================================")    
    
    
    
    
    
import math

def count_consecutive_above(data,threshold,n):
    if n <=0:
        return True     #trival case flag True
    
    current_streak = 0
    
    for x in data:
        if x > threshold:
            current_streak += 1
            if current_streak >= n:
                return True
        else:
            current_streak = 0
    
    return False     



# ------- Test Cases ------------
readings = [12.0, 15.5, 18.2, 19.0, 14.1, 21.0]

# Test 1 : looking for 2 consecutive values > 15.0
print(count_consecutive_above(readings, threshold= 15.0, n=2))
#output True

# Test 2 : looking for 4 consecutive values > 15.0 (Streak breaks at 141)
print(count_consecutive_above(readings, threshold = 15.0, n=4))
#output False
