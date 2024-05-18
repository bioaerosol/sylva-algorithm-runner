import os
import shutil
import subprocess
import tempfile
from enum import Enum

from sylva_algorithm_runner import AlgorithmRunOrder
from sylva_algorithm_runner.repositories.LogRepository import LogRepository


class RunSection(Enum):
    """ Enum for the different sections (aka steps) of an algorithm run. """
    CLONE = "CLONE"
    BUILD_ALGORITHM_IMAGE = "BUILD_ALGORITHM_IMAGE"
    BUILD_ALGORITHM_RUN_IMAGE = "BUILD_ALGORITHM_RUN_IMAGE"
    CLEANUP = "CLEANUP"


class Status(Enum):
    """ Enum for the different statuses of processes. """
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class AlgorithmRunner:
    """ Class to actually run an algorithm based on the given AlgorithmRunOrder. """
    pid = None
    log_repository = None
    algorithm_docker_image_name = None
    run_docker_image_name = None


    def __init__(self, configuration, pid, log_repository: LogRepository): 
        self.pid = pid
        self.log_repository = log_repository
        self.algorithm_docker_image_name = f"{self.pid}-algorithm:latest"
        self.run_docker_image_name = f"{self.pid}-run:latest"
        self.working_dir = os.path.join(configuration["path"], self.pid)


    def run(self, algorithm_run_order: AlgorithmRunOrder):
        """ Runs an algorithm based on the given AlgorithmRunOrder."""

        repo_name = algorithm_run_order.algorithmRepository
        repo_tag = algorithm_run_order.algorithmVersion

        os.makedirs(self.working_dir)

        self.log_repository.start_run(self.pid)

        # Clone algorithm from foreign repository
        clone_command = ["git", "clone", "-c", "advice.detachedHead=false", "--branch", f"{repo_tag}", f"https://github.com/{repo_name}.git", f"{self.working_dir}"]
        section_success = self.__run_and_log_section(RunSection.CLONE, clone_command)
        
        if not section_success:
            self.log_repository.end_run(self.pid, Status.FAILURE)
            return
        
        # Build algorithm docker image
        docker_build_algorithm_image = ["docker", "build", "-t", self.algorithm_docker_image_name, "."]
        section_success = self.__run_and_log_section(RunSection.BUILD_ALGORITHM_IMAGE, docker_build_algorithm_image)
        
        if not section_success:
            self.log_repository.end_run(self.pid, Status.FAILURE)
            return
        
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
            self.log_repository.end_run(self.pid, Status.FAILURE)
            return
        
        # Run the algorithm
        #TODO

        # Get the results
        #TODO

        self.log_repository.end_run(self.pid, Status.SUCCESS)
        return True


    def clean(self):
        """ Cleans up after running an algorithm. Removes the working directory and the docker images. """
        shutil.rmtree(self.working_dir)

        remove_algorithm_image = ["docker", "rmi", self.algorithm_docker_image_name]
        success = self.__run_and_log_section(RunSection.CLEANUP, remove_algorithm_image)
        
        remove_algorithm_run_image = ["docker", "rmi", self.run_docker_image_name]
        success = success and self.__run_and_log_section(RunSection.CLEANUP, remove_algorithm_run_image)
        
        return success


    def __run_and_log_section(self, run_section: RunSection, command: list) -> bool:
        """ Runs a command and logs the output to the given run_section in database. """
        self.log_repository.start_section(self.pid, run_section)
        
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, universal_newlines=True, cwd=self.working_dir, bufsize=1)

        for line in iter(process.stdout.readline, ""):
            self.log_repository.append_log(self.pid, run_section, line)      

        process.communicate()
        
        self.log_repository.set_section_status(self.pid, run_section, Status.SUCCESS if process.returncode == 0 else Status.FAILURE)

        self.log_repository.end_section(self.pid, run_section)

        return process.returncode == 0
