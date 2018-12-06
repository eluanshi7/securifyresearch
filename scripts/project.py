#!/usr/bin/env python3

"""
Author: Jakob Beckmann

Copyright 2018 ChainSecurity AG

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import sys
import abc
import json
import logging
import subprocess
import pathlib
import tempfile

import psutil
from . import utils


class Project(metaclass=abc.ABCMeta):
    """Abstract class implemented by projects using compilation and reporting.
    """
    securify_jar = pathlib.Path("build/libs/securify-0.1.jar")

    def __init__(self, project_root, clargs):
        """Sets the project root."""
        self.project_root = pathlib.Path(project_root)
        self.clargs = clargs

    def execute(self):
        """Execute the project. This includes compilation and reporting.

        This function returns 0 if no violations are found, and 1 otherwise.
        """
        with tempfile.TemporaryDirectory() as d:
            tmpdir = pathlib.Path(d)

            logging.warning("Compiling project")
            compilation_output = tmpdir / "comp.json"
            self.compile_(compilation_output)

            logging.warning("Running Securify")
            securify_target_output = tmpdir / "securify_res.json"
            self.run_securify(compilation_output, securify_target_output)

            return self.report(securify_target_output)

    def run_securify(self, compilation_output, securify_target_output):
        """Runs the securify command."""
        memory = psutil.virtual_memory().available // 1024 ** 3
        cmd = ["java", f"-Xmx{memory}G", "-jar", str(self.securify_jar),
               "-co", compilation_output,
               "-o", securify_target_output]
        if self.clargs.json:
            cmd += ["--json"]
        if self.clargs.verbose:
            cmd += ["-v"]
        if self.clargs.quiet:
            cmd += ["-q"]

        try:
            subprocess.run(cmd, check=True, stdout=sys.stdout,
                           stderr=sys.stderr, universal_newlines=True)
        except CalledProcessError as e:
            utils.handle_process_output_and_exit(e)


    @abc.abstractmethod
    def compile_(self, compilation_output):
        """Compile the project."""
        pass

    def report(self, securify_target_output):
        """Report findings.

        This function returns 0 if no violations are found, and 1 otherwise.
        """
        with open(securify_target_output) as file:
            json_report = json.load(file)

        for contract in json_report.values():
            for pattern in contract["results"].values():
                if pattern["violations"]:
                    return 1
        return 0
