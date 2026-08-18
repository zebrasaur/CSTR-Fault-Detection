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










def standardize(values):
    """Return values as (x - mean) / standard_deviation, as a list.
    Use the sample standard deviation (divide by n-1)."""
    
def count_consecutive_above(values, threshold, n):
    """Return True if at leas 'n' consecutive values exceed 'threshold'."""
    