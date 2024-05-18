import requests

from sylva_algorithm_runner import AlgorithmRunOrder

class GitHubRepository:
    """ This class is responsible for reading the configuration and the algorithm run orders from the GitHub repository. It also provides a method to get the tag for a public release. """
    configuration = None

    def __init__(self, github_configuration: dict = None) -> None:        
        self.configuration = github_configuration

    def get_current_run_orders(self):
        """ Reads the algorithm run orders from the GitHub repository and returns them as a list. """
        response = self.__read_api(f"https://api.github.com/repos/{self.configuration['repository']}/branches/main")
        tree_url = response["commit"]["commit"]["tree"]["url"]

        response = self.__read_api(tree_url)
        blobs = self.__get_yamls(response["tree"])
        
        algorithmRunOrders = []
        for id, blob in blobs.items():
            algorithmOrder = AlgorithmRunOrder.from_source(id, blob)
            algorithmRunOrders.append(algorithmOrder)

        return algorithmRunOrders
    

    def get_tag_for_public_release(self, repository, version) -> str:
        """ Reads the public releases from the GitHub repository and returns the tag for the given version (which should be the given version). """
        response = self.__read_public_api(f"https://api.github.com/repos/{repository}/releases")
        
        try: 
            for entry in response:
                if entry["tag_name"] == version:
                    return entry["tag_name"]
        except:
            # no-op by intention, we just pass to return None
            pass
            
        return None


    def __read_public_api(self, path):
        headers = {            
            'X-GitHub-Api-Version': '2022-11-28',
            'Accept': 'application/vnd.github+json'
        }
        return requests.get(f'{path}', headers=headers).json()


    def __read_api(self, path):
        """ Reads the GitHub API with the given path and returns the JSON response. """
        headers = {
            'Authorization': f'token {self.configuration["token"]}',
            'X-GitHub-Api-Version': '2022-11-28',
            'Accept': 'application/vnd.github+json'
        }
        return requests.get(f'{path}', headers=headers).json()


    def __read_blob(self, path):
        try:
            headers = {
                'Authorization': f'token {self.configuration["token"]}',
                'X-GitHub-Api-Version': '2022-11-28',
                'Accept': 'application/vnd.github.raw+json'
            }
            return requests.get(f'{path}', headers=headers).text
        except Exception as e:
            return None


    def __get_yamls(self, tree):
        blobs = {}
        for item in tree:
            if item["type"] == "blob" and item["path"].endswith(".yaml"):
                blob = self.__read_blob(item["url"])
                if blob is not None:
                    blobs[item["url"]] = blob

            elif item["type"] == "tree":
                blobs = {**blobs, **self.__get_yamls(self.__read_api(item["url"])["tree"])}
        return blobs
