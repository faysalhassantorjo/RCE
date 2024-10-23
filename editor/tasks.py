# from celery import shared_task

# import subprocess

# @shared_task
# def run_code_task(code):
#         """Run the provided Python code in a subprocess and capture the output."""
#         try:
#             # Run the code using a subprocess and capture output
#             result = subprocess.run(
#                 ['python', '-c', code],
#                 text=True,  # Ensure result is returned as string
#                 capture_output=True,  # Capture both stdout and stderr
#                 check=True  # Raise exception if command fails
#             )
#             return result.stdout  # Return the standard output of the code
#         except subprocess.CalledProcessError as e:
#             return e.stderr  # Return error output if the code fails

import subprocess
import sys
import time
import logging
logger = logging.getLogger(__name__)
from celery import shared_task

@shared_task
def run_code_task(code):
    """Run the provided Python code in a subprocess and capture the output."""
    # logger.info("Task started, delaying for 5 seconds...")
    # time.sleep(10)
    # logger.info("Task ended, delaying for 5 seconds...")
    
    try:
        # Use sys.executable to get the path to the current Python interpreter
        result = subprocess.run(
            [sys.executable, '-c', code],
            text=True,
            capture_output=True,
            check=True
        )
        return result.stdout  # Return the standard output of the code
    except subprocess.CalledProcessError as e:
        return e.stderr  # Return error output if the code fails

def run_code_fn(code):
    """Run the provided Python code in a subprocess and capture the output."""
    # logger.info("Task started, delaying for 5 seconds...")
    # time.sleep(10)
    # logger.info("Task ended, delaying for 5 seconds...")
    
    try:
        # Use sys.executable to get the path to the current Python interpreter
        result = subprocess.run(
            [sys.executable, '-c', code],
            text=True,
            capture_output=True,
            check=True
        )
        return result.stdout  # Return the standard output of the code
    except subprocess.CalledProcessError as e:
        return e.stderr  # Return error output if the code fails