# SYLVA Algorithm Runner

Debian package that provides all components to manage, run and evaluate algorithms. Furthermore, a simple backend application provides REST endpoints to get status of algorithm runs.

For detailed software concept please refer to SYLVA software documentation.

# Object Model
## Run Order
A Run Order is a definition of an algorithm to run with its version and GitHub repository to get it from. 

Furthermore, a dataset is defined which identifies the level-0 data to be processed by the algorithm. If it is referenced by name the data will be retrieved from SYLVA Data Portal API where a dataset with this name must be maintained. If it is referenced by local path the data is expected at the given path on the machine which runs the algorithm.

Run orders are retrieved from a GitHub repository and defined in YAML files such as
```yaml
algorithm:
  name: <user friendly name of algorithm>
  repository: <public GitHub repository>
  version: <released version of algorithm>
dataset: 
  name: <dataset name to run with>
  # or 
  localpath: <local path where to find the files to run with>
```

## Linux API
Two commands are provided:
- sylva-algorithm-upgrade-run-orders – Connects to GitOps repository and scans for new run orders.
- sylva-algorithm-run <id> – Runs the run order with given ID.

# Development
This section gives some information to develop this package. As it is a Debian package you need a Debian-like operating system to build, test and run it.

## Requirements
To develop and build this Debian package you need to have installed following requirements:
- debhelper
- build-essential
- dh-python
- python3-all
- python3-pip

## Build
```dpkg-buildpackage -b```