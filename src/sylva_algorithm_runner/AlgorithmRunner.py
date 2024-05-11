import os
import shutil
import subprocess

from sylva_algorithm_runner import AlgorithmRunOrder

class AlgorithmRunner:
    configuration = None
    pid = None
    algorithm_docker_image_name = None
    run_docker_image_name = None

    def __init__(self, configuration, pid):
        self.configuration = configuration    
        self.pid = pid
        self.algorithm_docker_image_name = f"{self.pid}-algorithm:latest"
        self.run_docker_image_name = f"{self.pid}-run:latest"

    def run(self, algorithm_run_order: AlgorithmRunOrder):
        folder_path = os.path.join(self.configuration["path"], self.pid)
        os.makedirs(folder_path)

        repo_name = algorithm_run_order.algorithmRepository
        repo_tag = algorithm_run_order.algorithmVersion

        clone_command = ["git", "clone", "-c", "advice.detachedHead=false", "--branch", f"{repo_tag}", f"https://github.com/{repo_name}.git", f"{folder_path}"]
        
        (stdout, stderr) = subprocess.Popen(clone_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, universal_newlines=True).communicate()
        print(stdout)
        print(stderr)

        (stdout, stderr) = subprocess.Popen(["docker", "build", "-t", self.algorithm_docker_image_name, "."], cwd=folder_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, universal_newlines=True).communicate()
        print(stdout)
        print(stderr)

        with open('/var/lib/sylva-algorithm-runner/Dockerfile.template', 'r') as file:
            dockerfile_template = file.read()

        dockerfile_content = dockerfile_template.replace('{{pid}}', self.pid)

        (stdout, stderr) = subprocess.Popen(["docker", "build", "-t", self.run_docker_image_name, "-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, universal_newlines=True).communicate(
            input=dockerfile_content
        )
        print(stdout)
        print(stderr)

    def clean(self):
        folder_path = os.path.join(self.configuration["path"], self.pid)
        shutil.rmtree(folder_path)

        (stdout, stderr) = subprocess.Popen(["docker", "rmi", self.algorithm_docker_image_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, universal_newlines=True).communicate()
        print(stdout)
        print(stderr)

        (stdout, stderr) = subprocess.Popen(["docker", "rmi", self.run_docker_image_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, universal_newlines=True).communicate()
        print(stdout)
        print(stderr)
