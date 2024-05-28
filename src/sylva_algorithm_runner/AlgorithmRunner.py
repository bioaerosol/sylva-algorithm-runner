import os
import shutil
import subprocess
import tempfile
from enum import Enum

from sylva_algorithm_runner import AlgorithmRunOrder
from sylva_algorithm_runner.repositories.LogRepository import LogRepository
import json


class RunSection(Enum):
    """ Enum for the different sections (aka steps) of an algorithm run. """
    ORDER_DATA = "ORDER_DATA"
    CLONE = "CLONE"
    BUILD_ALGORITHM_IMAGE = "BUILD_ALGORITHM_IMAGE"
    BUILD_ALGORITHM_RUN_IMAGE = "BUILD_ALGORITHM_RUN_IMAGE"
    CLEANUP = "CLEANUP"
    START = "START"
    RUN_ALGORITHM = "RUN_ALGORITHM"
    COPY_OUTPUT = "COPY_OUTPUT"
    CLEANUP_CONTAINER = "CLEANUP_CONTAINER"

class Status(Enum):
    """ Enum for the different statuses of processes. """
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    WAITING_FOR_DATA = "WAITING_FOR_DATA"


class AlgorithmRunner:
    """ Class to actually run an algorithm based on the given AlgorithmRunOrder. """
    pid = None
    log_repository = None
    algorithm_docker_image_name = None
    run_docker_image_name = None
    dataportal_configuration = None


    def __init__(self, runner_configuration, dataportal_configuration, pid, log_repository: LogRepository): 
        self.pid = pid
        self.log_repository = log_repository
        self.algorithm_docker_image_name = f"{self.pid}-algorithm:latest"
        self.run_docker_image_name = f"{self.pid}-run:latest"
        self.working_dir = os.path.join(runner_configuration["path"], self.pid)
        self.dataportal_configuration = dataportal_configuration


    def run(self, algorithm_run_order: AlgorithmRunOrder):
        """ Runs an algorithm based on the given AlgorithmRunOrder."""

        repo_name = algorithm_run_order.algorithmRepository
        repo_tag = algorithm_run_order.algorithmVersion

        os.makedirs(self.working_dir)

        self.log_repository.start_run()

        try:
            # start with ordering data as this may take some minutes
            curl_command = ["curl", "-s", "-X", "POST", self.dataportal_configuration["workspace"], "-H", "Content-Type: application/json", "-d", json.dumps({"dataset": algorithm_run_order.dataset, "token": self.dataportal_configuration["token"]})]
            response = self.__run_and_log_section(RunSection.ORDER_DATA, curl_command, return_response_if_success=True)

            if response == False:
                raise Exception()
            else:
                # response might contain our workspace id
                workspace_id = json.loads(response)["id"]
                self.log_repository.log_workspace_id(workspace_id)
            
            # Clone algorithm from foreign repository
            clone_command = ["git", "clone", "-c", "advice.detachedHead=false", "--branch", f"{repo_tag}", f"https://github.com/{repo_name}.git", f"{self.working_dir}"]
            section_success = self.__run_and_log_section(RunSection.CLONE, clone_command)
            
            if not section_success:
                raise Exception()
            
            # Build algorithm docker image
            docker_build_algorithm_image = ["docker", "build", "-t", self.algorithm_docker_image_name, "."]
            section_success = self.__run_and_log_section(RunSection.BUILD_ALGORITHM_IMAGE, docker_build_algorithm_image)
            
            if not section_success:
                raise Exception()
            
            # Build run docker image (based on algorithm docker image + own extension to make it work); Dockerfile for this is part of this package
            with open('/var/lib/sylva-algorithm-runner/Dockerfile.template', 'r') as file:
                dockerfile_template = file.read()

            dockerfile_content = dockerfile_template.replace('{{pid}}', self.pid)

            with tempfile.TemporaryDirectory() as tmpdirname:
                with open(os.path.join(tmpdirname, "Dockerfile"), "w") as dockerfile:
                    dockerfile.write(dockerfile_content)
                    dockerfile.flush()
                    
                    docker_build_algorithm_run_image = ["docker", "build", "-t", self.run_docker_image_name, tmpdirname]
                    section_success = self.__run_and_log_section(RunSection.BUILD_ALGORITHM_RUN_IMAGE, docker_build_algorithm_run_image)

            if not section_success:
                raise Exception()
            
            # Run the algorithm
            docker_run = ["docker", "run", "-d", "--name", "algorithm_container", self.run_docker_image_name]
            section_success = self.__run_and_log_section(RunSection.START, docker_run)
            if not section_success:
                raise Exception()
            
            docker_run = ["docker", "logs", "--follow", "algorithm_container"]
            section_success = self.__run_and_log_section(RunSection.RUN_ALGORITHM, docker_run)
            if not section_success:
                raise Exception()
            
            docker_run = ["docker", "wait", "algorithm_container"]
            section_success = self.__run_and_log_section(RunSection.RUN_ALGORITHM, docker_run)
            if not section_success:
                raise Exception()

            # Get the results
            #TODO

            # last step: clean-up
            section_success = self.__clean()
            self.log_repository.end_run(Status.SUCCESS if section_success else Status.FAILURE)
            
            return section_success
        
        except:
            self.__clean()
            self.log_repository.end_run(Status.FAILURE)


    def __clean(self):
        """ Cleans up after running an algorithm. Removes the working directory and the docker images. """
        remove_algorithm_container = ["docker", "rm", "algorithm_container"]
        success3 = self.__run_and_log_section(RunSection.CLEANUP, remove_algorithm_container)

        remove_algorithm_run_image = ["docker", "rmi", self.run_docker_image_name]
        success2 = self.__run_and_log_section(RunSection.CLEANUP, remove_algorithm_run_image)

        remove_algorithm_image = ["docker", "rmi", self.algorithm_docker_image_name]
        success1 = self.__run_and_log_section(RunSection.CLEANUP, remove_algorithm_image)
                
        shutil.rmtree(self.working_dir)

        return success1 and success2 and success3


    def __run_and_log_section(self, run_section: RunSection, command: list, return_response_if_success: bool = False):
        """ Runs a command and logs the output to the given run_section in database. """
        self.log_repository.start_section(run_section)
        
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, universal_newlines=True, cwd=self.working_dir, bufsize=1)

        response = ""
        for line in iter(process.stdout.readline, ""):
            response += line
            self.log_repository.append_log(run_section, line)      

        process.communicate()
        
        self.log_repository.set_section_status(run_section, Status.SUCCESS if process.returncode == 0 else Status.FAILURE)

        self.log_repository.end_section(run_section)

        if return_response_if_success and process.returncode == 0:
            return response
        else:
            return process.returncode == 0
