# Python Program to solve House Robber Problem using Recursion

# Calculate the maximum stolen value recursively
def maxLootRec(hval, n):
    
    # If no houses are left, return 0.
    if n <= 0:
        return 0
  
    # If only 1 house is left, rob it. 
    if n == 1:
        return hval[0]

    # Two Choices: Rob the nth house and do not rob the nth house 
    pick = hval[n - 1] + maxLootRec(hval, n - 2)
    notPick = maxLootRec(hval, n - 1)

    # Return the max of two choices
    return max(pick, notPick)

# Function to calculate the maximum stolen value
def maxLoot(hval):
    n = len(hval)
  
    # Call the recursive function for n houses
    return maxLootRec(hval, n)

if __name__ == "__main__":
    hval = [6, 7, 1, 3, 8, 2, 4]
    print(maxLoot(hval))