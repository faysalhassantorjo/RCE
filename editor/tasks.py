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
from django.shortcuts import get_object_or_404
from .models import *
import docker
import shlex
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

client = docker.from_env()


@shared_task
def run_code_task(code, inputs=None, code_executed_by=None, room_name=None):
    try:
        usr = User.objects.get(username=code_executed_by)
        userprofile = UserProfile.objects.get(user=usr)
        user_container = get_object_or_404(UserContainer, user=userprofile)
    except UserProfile.DoesNotExist:
        return "Error: UserProfile does not exist."

    try:
        container = client.containers.get(user_container.container_id)
        exec_cmd = f'python3 -c {shlex.quote(code)}'
        exit_code, output = container.exec_run(exec_cmd)
        output_decoded = output.decode()

        channel_layer = get_channel_layer()
        group_name = f"task_{room_name}"

        try:
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "task.update", 
                    "output": output_decoded,
                    "code_executed_by": code_executed_by,
                }
            )
            return f"Message sent to group {group_name}"
        except Exception as send_error:
            return f"Error sending message to group: {send_error}"
            
        return output_decoded
    except Exception as e:
        return f'Exception: {e}, Container Status: {container.status}'






# @shared_task
# def run_code_task(code,inputs=None):
#     # Convert Windows path to WSL path
#     python_executable = "/mnt/d/RCE/packages/user_1/Scripts/python.exe"
    
#     # Debugging log
#     logger.info(f"Checking Python executable at {python_executable}")
    
#     # Ensure the executable exists
#     if not os.path.isfile(python_executable):
#         return f"Python executable not found at {python_executable} (cwd={os.getcwd()}, PATH={os.environ['PATH']})."

#     # Modify environment to ensure PATH is correct
#     env = os.environ.copy()
#     env["PATH"] = os.path.dirname(python_executable) + ":" + env["PATH"]

#     try:
#         # simulated_input = "\n".join(inputs)
#         result = subprocess.Popen(
#             [python_executable, "-c", code],
#             text=True,
#             # capture_output=True,
#             # check=True,
#             env=env,
#             stdin=subprocess.PIPE,
#             stdout=subprocess.PIPE,
#             stderr=subprocess.PIPE
#         )
#         stdout, stderr = result.communicate(input=inputs)
#         return stdout
#     except subprocess.CalledProcessError as e:
#         return e.stderr



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
    
    
# @shared_task
# def install_package(package_name, user_env_path):
#     try:
#         # Run pip install in the user's isolated environment
#         subprocess.check_output(
#             [user_env_path, "install", package_name],
#             stderr=subprocess.STDOUT
#         )
#         return {"success": True, "message": f"Package '{package_name}' installed successfully."}
#     except subprocess.CalledProcessError as e:
#         return {"success": False, "message": e.output.decode()}
import os , platform
def get_pip_path(user_env_path):
    if platform.system() == "Windows":
        return os.path.join(user_env_path, "Scripts", "pip.exe")
    else:
        return os.path.join(user_env_path, "bin", "pip")
def install_package(package_name, user_env_path):
    pip_path = get_pip_path(user_env_path)
    try:
        print(f"Using pip at: {pip_path}")
        result = subprocess.check_output([pip_path, "install", package_name], stderr=subprocess.STDOUT)
        print('Successfully installed')
    except FileNotFoundError:
        print(f'File not found: {pip_path}')
    except subprocess.CalledProcessError as e:
        print(f'Subprocess called error: {e.output.decode()}')
