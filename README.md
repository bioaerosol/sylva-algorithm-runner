# SYLVA Algorithm Runner

Debian package that provides all components to manage, run and evaluate algorithms. Furthermore, a simple backend application provides REST endpoints to get status of algorithm runs.

For detailed software concept please refer to SYLVA software documentation.

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