import os
import shutil
import subprocess
import tempfile
from enum import Enum

from sylva_algorithm_runner import AlgorithmRunOrder
from sylva_algorithm_runner.repositories.LogRepository import LogRepository
import json
import requests

class RunSection(Enum):
    """ Enum for the different sections (aka steps) of an algorithm run. """
    ORDER_DATA = "ORDER_DATA"
    CLONE = "CLONE"
    BUILD_ALGORITHM_IMAGE = "BUILD_ALGORITHM_IMAGE"
    BUILD_ALGORITHM_RUN_IMAGE = "BUILD_ALGORITHM_RUN_IMAGE"
    WAIT_FOR_DATA = "WAIT_FOR_DATA"
    START_ALGORITHM = "START_ALGORITHM"
    RUN_ALGORITHM = "RUN_ALGORITHM"
    WAIT_FOR_ALGORITHM = "WAIT_FOR_ALGORITHM"
    COPY_OUTPUT = "COPY_OUTPUT"
    CLEANUP = "CLEANUP"

class Status(Enum):
    """ Enum for the different statuses of processes. """
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    WAITING_FOR_DATA = "WAITING_FOR_DATA"


class AlgorithmRunner:
    """ Class to actually run an algorithm based on the given AlgorithmRunOrder. """
    dataportal_configuration = None
    runner_configuration = None
    database_configuration = None
    log_repository = None

    algorithm_docker_image_name = None
    run_docker_image_name = None
    workspace_id = None


    def __init__(self, runner_configuration, dataportal_configuration, database_configuration): 
        self.dataportal_configuration = dataportal_configuration
        self.runner_configuration = runner_configuration
        self.database_configuration = database_configuration
        self.log_repository = LogRepository(self.database_configuration, True)


    def __init_run(self, pid: str, workspace_id: str = None):
        self.pid = pid
        self.algorithm_docker_image_name = f"{self.pid}-algorithm:latest"
        self.run_docker_image_name = f"{self.pid}-run:latest"
        self.working_dir = os.path.join(self.runner_configuration["path"], self.pid)
        self.workspace_id = workspace_id


    def run(self, algorithm_run_order: AlgorithmRunOrder):
        """ Runs an algorithm based on the given AlgorithmRunOrder."""
        existing_run = self.log_repository.get_waiting_for_data(algorithm_run_order)

        try:
            if (existing_run is None):
                # first time we run this algorithm
                id = self.log_repository.start_run(algorithm_run_order)
                self.__init_run(id)
                
                os.makedirs(self.working_dir)

                self.__create_and_prepare_run(algorithm_run_order)
                self.log_repository.start_section(self.pid, RunSection.WAIT_FOR_DATA)

            else:
                self.__init_run(str(existing_run["_id"]), existing_run["workspace"])
                self.workspace_id = existing_run["workspace"]
            
            data_available = self.__check_data_available()
            
            if (not data_available):
                self.log_repository.set_status(self.pid, Status.WAITING_FOR_DATA)
            else:
                workspace_path = self.runner_configuration['workspace']
                
                if not os.path.exists(workspace_path):
                    self.log_repository.append_log(self.pid, RunSection.WAIT_FOR_DATA, "Workspace not found where expected.")
                    self.log_repository.end_section(self.pid, RunSection.WAIT_FOR_DATA, Status.FAILURE)
                    raise Exception()
                
                else:
                    self.log_repository.end_section(self.pid, RunSection.WAIT_FOR_DATA, Status.SUCCESS)
                    self.log_repository.set_status(self.pid, Status.RUNNING)
                    self.__run_algorithm(workspace_path)

        except:
            self.__clean()
            self.log_repository.end_run(self.pid, Status.FAILURE)


    def __create_and_prepare_run(self, algorithm_run_order: AlgorithmRunOrder):
        """ Creates a new run and prepares it based on the given AlgorithmRunOrder. """        
        
        # start with ordering data as this may take some minutes; API of SYLVA Data Portal is used
        curl_command = ["curl", "-s", "-X", "POST", self.dataportal_configuration["workspace"], "-H", "Content-Type: application/json", "-d", json.dumps({"dataset": algorithm_run_order.dataset, "token": self.dataportal_configuration["token"]})]
        response = self.__run_and_log_section(RunSection.ORDER_DATA, curl_command, return_response_if_success=True)

        if response == False:
            raise Exception()
        else:
            # response might contain our workspace id if it was not False
            self.workspace_id = json.loads(response)["id"]
            self.log_repository.log_workspace_id(self.pid, self.workspace_id)
        


        # Clone algorithm from foreign algorithm repository
        clone_command = ["git", "clone", "-c", "advice.detachedHead=false", "--branch", f"{algorithm_run_order.algorithmVersion}", f"https://github.com/{algorithm_run_order.algorithmRepository}.git", f"{self.working_dir}"]
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
        dockerfile_content = dockerfile_content.replace('{{workspaceId}}', self.workspace_id)

        with tempfile.TemporaryDirectory() as tmpdirname:
            with open(os.path.join(tmpdirname, "Dockerfile"), "w") as dockerfile:
                dockerfile.write(dockerfile_content)
                dockerfile.flush()
                
                docker_build_algorithm_run_image = ["docker", "build", "-t", self.run_docker_image_name, tmpdirname]
                section_success = self.__run_and_log_section(RunSection.BUILD_ALGORITHM_RUN_IMAGE, docker_build_algorithm_run_image)

        if not section_success:
            raise Exception()       
    

    def __run_algorithm(self, workspace_path: str):
        # Run the algorithm
        
        mountpoint = f"type=bind,source={workspace_path},destination=/data/workspace/,readonly"
        docker_run = ["docker", "run", "--mount", mountpoint, "-d", "--name", "algorithm_container", self.run_docker_image_name]
        section_success = self.__run_and_log_section(RunSection.START_ALGORITHM, docker_run)

        if not section_success:
            raise Exception()
        

        
        docker_logs = ["docker", "logs", "--follow", "algorithm_container"]
        section_success = self.__run_and_log_section(RunSection.RUN_ALGORITHM, docker_logs)
        if not section_success:
            raise Exception()
        


        # block until containers stop, then print exit codes which must be "0" for success
        docker_wait = ["docker", "wait", "algorithm_container"]
        section_success = self.__run_and_log_section(RunSection.WAIT_FOR_ALGORITHM, docker_wait, return_response_if_success=True)
        
        if section_success == False or section_success.strip() != "0":
            # set status of RUN_ALGORITHM manually as __run_and_log_section is not able to detect the exit code
            self.log_repository.end_section(self.pid, RunSection.RUN_ALGORITHM, Status.FAILURE)
            raise Exception()
        


        # Get the results
        output_folder = os.path.join(self.runner_configuration['output'], self.pid)
        os.makedirs(output_folder)
        copy_output = ["docker", "cp", "algorithm_container:/data/output/.", output_folder]
        section_success = self.__run_and_log_section(RunSection.COPY_OUTPUT, copy_output)

        if not section_success:
            raise Exception()

        # log the output files
        file_list = []
        for root, dirs, files in os.walk(output_folder):
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path)
                file_info = {"fileName": file, "filePath": file_path[len(output_folder)+1:], "fileSize": file_size}
                file_list.append(file_info)

        self.log_repository.log_output_files(self.pid, file_list)

        # last step: clean-up
        section_success = self.__clean()
        self.log_repository.end_run(self.pid, Status.SUCCESS if section_success else Status.FAILURE)
        
        return section_success


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
        self.log_repository.start_section(self.pid, run_section)
        
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, universal_newlines=True, cwd=self.working_dir, bufsize=1)

        response = ""
        for line in iter(process.stdout.readline, ""):
            response += line
            self.log_repository.append_log(self.pid, run_section, line)      

        process.communicate()
        
        self.log_repository.end_section(self.pid, run_section, Status.SUCCESS if process.returncode == 0 else Status.FAILURE)

        if return_response_if_success and process.returncode == 0:
            return response
        else:
            return process.returncode == 0


    def __check_data_available(self) -> bool:
        """ Checks if the requested data is available. Returns True if it is, False otherwise. Raises an exception if the data is not available anymore. """

        response = requests.get(f"https://data.sylva.bioaerosol.eu/api/workspace/{self.workspace_id}?token={self.dataportal_configuration['token']}")

        if response.status_code == 200:
            data = response.json()

            if (data.get("status") == "expired"):
                self.log_repository.append_log(self.pid, RunSection.WAIT_FOR_DATA, "Requested data is not available anymore.")
                self.log_repository.end_section(self.pid, RunSection.WAIT_FOR_DATA, Status.FAILURE)
                raise Exception()
            
            if data.get("status") == "provided":
                self.log_repository.append_log(self.pid, RunSection.WAIT_FOR_DATA, "Data provided.")
                return True
            
        self.log_repository.append_log(self.pid, RunSection.WAIT_FOR_DATA, "Requested data not available yet.")
        return False