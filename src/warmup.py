import math


def moving_average(data: list[float], window_size: int):
    """Return a list of averages over each consecutive 'window' values.
    Result is shorter than the input by (window - 1)."""
    
    # 1. Guard aginst invalid inputs
    if window_size <= 0:
        raise ValueError("Window size must be at least 1.")
    if len(data) < window_size:
        return[] # not enough data points to form a single window
    
    moving_averages = []
    
    # 2. Slide the window across the dataset
    #len(data) - window_size +1 ensures the loop stops before running off the end
    for i in range(len(data) - window_size + 1):
        # Extract the current slice
        current_window = data[i : i + window_size]
        
        #calculate the average of this window
        window_average = sum(current_window) / window_size
        
        #store the result
        moving_averages.append(round(window_average, 2))
        
    return moving_averages

    # ---- test the function-------------
    
prices = [100.0, 102.5, 101.0, 105.0, 107.5, 106.0, 110.0]
window = 3
result = moving_average(prices, window)
    
print(f"orgininal data: {prices}")
print(f"3-period moving average: {result}")
print(f"========================================================")
print(f"========================================================")




def standardize(data: list[float]) -> list[float]:
    """ Return values as (x - mean) / standard_deviation, as a list.
    Use the sample standard deviation (divide by n-1).
    """
    n = len(data)
    
    # Step 1: input validation  
    #Dividing by (n-1) requires at least 2 data points
    if n < 2:
        raise ValueError("At least 2 data points are required to standardize.")
    
    #Step 2 : calculate the mean
    mean = sum(data)/n 

    #step 3 : calculate the sum of squared differences from the mean
    #sum((x - mean)^2)
    
    squared_diff_sum = sum(( x - mean) ** 2 for x in data)

    # Step 4 ; CALCULATE SAMPLE VARIANCE (DIVIDE BY N-1) AND STANDARD DEVIATION
    
    sample_variance = squared_diff_sum / (n-1)
    sample_std = math.sqrt(sample_variance)

    # Guard aginst dividing by zero if all values in the list are identical
    if sample_std == 0:
        raise ValueError("Standard deviation is zero (all numbers are identical).")

    #Step 5: Calculate (x - mean) / s for every value
    standardized_list = [(x-mean) / sample_std for x in data]
    return standardized_list

# ------------------ Test the function ---------------------------

raw_data = [10.0, 12.0, 23.0, 16.0, 23.0, 21.0, 16.0]
z_scores = standardize(raw_data)

print(f"orginal Data: {raw_data}")
print("Z-scores:")
for orig, z in zip(raw_data, z_scores):
    print(f" value: {orig:>4} --> Z-Score: {z: .4f}")
    
print(f"========================================================")
print(f"========================================================")    
    
    
    
    
    
def count_consecutive_above(data: list[float], threshold: float, n: int) -> bool:
    """Return True if at leas 'n' consecutive values exceed 'threshold'."""

    # Guard: 0 or negative required streak is immediately satisfied.
    if n <= 0:
        return True

    current_streak = 0

    for value in data:
        if value > threshold:
            current_streak += 1
            # check if we hit the target streak
            if current_streak >= n:
                return True
        else:
            # The streak broke; reset counter
            current_streak = 0
    # Looked through all numbers and never reached 'n' in a row
    return False

# ------- Test Cases ------------
readings = [12.0, 15.5, 18.2, 19.0, 14.1, 21.0]

# Test 1 : looking for 2 consecutive values > 15.0
print(count_consecutive_above(readings, threshold= 15.0, n=2))
#output True

# Test 2 : looking for 4 consecutive values > 15.0 (Streak breaks at 141)
print(count_consecutive_above(readings, threshold = 15.0, n=4))
#output False
