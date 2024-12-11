import os

path = r"D:\\RCE\\packages\\user_1\\Scripts\\python.exe"
if os.path.isfile(path):
    print(f"Python executable found at {path}")
else:
    print(f"Python executable not found at {path}")
