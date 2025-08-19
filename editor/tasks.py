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
import tarfile,io
import socket
client = docker.from_env()
import re
import base64

@shared_task
def run_code_task(code, inputs=None, code_executed_by=None, room_name=None, language=None, from_test_editor=False, test_eidtor_channel_name=None):
    try:

        # Get container
        try:
            usr = User.objects.get(username=code_executed_by)
            userprofile = UserProfile.objects.get(user=usr)
            user_container = UserContainer.objects.get(user=userprofile)
            container = client.containers.get(user_container.container_id)
        except Exception:
            container = client.containers.get('realtime_code_editor-environment-1')

        # Prepare communication
        channel_layer = get_channel_layer()
        group_name = f"task_{room_name}"

        result_output = ""
        error_output = ""
        exit_code = -1

        if language == "PYTHON":
            filename = f"{code_executed_by}_file.py"
            input_filename = f"{code_executed_by}_input.txt"

            # Step 1: Write the code file
            encoded_code = base64.b64encode(code.encode()).decode()
            write_code_cmd = f"bash -c 'echo {encoded_code} | base64 -d > /code_file/{filename}'"
            container.exec_run(write_code_cmd)

            # Step 2: Handle input if provided
            if inputs and inputs.strip():
                encoded_input = base64.b64encode(inputs.encode()).decode()
                input_cmd = f"bash -c 'echo {encoded_input} | base64 -d > /code_file/{input_filename}'"
                container.exec_run(input_cmd)
                # exec_cmd = f"bash -c timeout --kill-after=2s 5s python3 {filename} < {input_filename}"
                exec_cmd = f"bash -c 'timeout --kill-after=2s 5s python3 {filename} < {input_filename}'"

            else:
                exec_cmd = f"timeout --kill-after=2s 5s python3 {filename}"

            # Step 3: Run the code
            exit_code, output = container.exec_run(
                exec_cmd,
                tty=False,
                demux=True,
                workdir="/code_file",
                environment={'PYTHONUNBUFFERED': '1'}
            )

        
        elif language == "C":
            filename = f"{code_executed_by}_file.c"
            binary_name = f"{code_executed_by}_a.out"

            # Write C code to file
            encoded = base64.b64encode(code.encode()).decode()
            write_cmd = f"bash -c 'echo {encoded} | base64 -d > /code_file/{filename}'"
            container.exec_run(write_cmd)

            # Compile C code
            compile_cmd = f"gcc -o {binary_name} {filename}"
            compile_exit_code, compile_output = container.exec_run(
                compile_cmd,
                workdir="/code_file",
                demux=True
            )

            stdout, stderr = compile_output
            stdout = stdout.decode(errors='ignore') if stdout else ""
            stderr = stderr.decode(errors='ignore') if stderr else ""

            if compile_exit_code != 0:
                final_output = f"[COMPILATION ERROR]: {stderr or 'Unknown compilation error.'}"
                async_to_sync(channel_layer.group_send)(
                    group_name,
                    {
                        "type": "task.update",
                        "output": final_output,
                        "code_executed_by": code_executed_by,
                    }
                )
                return

            # Run the binary with timeout
            exec_cmd = f"timeout --kill-after=2s 5s ./{binary_name}"
            exit_code, output = container.exec_run(
                exec_cmd,
                tty=False,
                demux=True,
                workdir="/code_file"
            )
        
        
        stdout, stderr = output
        result_output = stdout.decode(errors='ignore') if stdout else ""
        error_output = stderr.decode(errors='ignore') if stderr else ""

        # Build final message
        if exit_code == 124:
            final_output = "[TIMEOUT] Execution exceeded 10 seconds.\n"
        elif error_output:
            final_output = f"[ERROR]: {error_output}"
        else:
            final_output = result_output or "[INFO] No output."

        
        if from_test_editor:
            async_to_sync(channel_layer.send)(
                test_eidtor_channel_name,
                {
                    "type": "test_editor_update",
                    "output": final_output,
                    "code_executed_by": code_executed_by,
                }
            )
            
        else:
        # Send once to WebSocket
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "task.update",
                    "output": final_output,
                    "code_executed_by": code_executed_by,
                }
            )

    except Exception as e:
        fallback_output = f"[FATAL ERROR] {str(e)}"
        async_to_sync(channel_layer.group_send)(
            f"task_{room_name}",
            {
                "type": "task.update",
                "output": fallback_output,
                "code_executed_by": code_executed_by,
            }
        )
        
        
@shared_task
def stop_container_task(container_id):
    try:
        # container = client.containers.get(container_id)
        # container.stop()
        return f"Container {container_id} stopped successfully."
    except Exception as e:
        return f"Error stopping container {container_id}: {e}"
    

@shared_task
def finish_lab_test(test_id):
    obj = LabTest.objects.get(id = test_id)
    obj.available = False
    obj.save()
    return "Lab test is Finished!"



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
        
        

