# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2019, 2021-2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""KernelCI Runtime environment base class definition"""

import abc
import importlib
import json
import os
import yaml

from jinja2 import Environment, FileSystemLoader


def add_kci_raise(jinja2_env):
    """Add a kci_raise function to use in templates

    This adds a `kci_raise` function to a given Jinja2 environment `jinja2_env`
    so it can be used to raise exceptions from template files when for example
    some template parameters are not valid.
    """
    def template_exception(msg):
        raise Exception(msg)
    jinja2_env.globals['kci_raise'] = template_exception


class Job:
    """Pipeline job"""

    def __init__(self, node, job_config):
        """A Job object can be run using a Runtime environment

        A pipeline Job object can be used with a Runtime to generate a job
        definition and keep track of all the related pieces of data such as the
        configuration from YAML and the API node.

        *node* is the node data for the job from the API
        *job_config* is the Job configuration object loaded from YAML
        """
        self._node = node
        self._config = job_config
        self._platform_config = None  # node['extra']['platform'] ?
        self._storage_config = None  # node['extra']['storage'] ?

    @property
    def node(self):
        """Node data for this job"""
        return self._node

    @property
    def config(self):
        """Configuration for this job loaded from YAML"""
        return self._config

    @property
    def name(self):
        """Name of the job"""
        return self.config.name

    @property
    def platform_config(self):
        """Target platform configuration loaded from YAML"""
        return self._platform_config

    @platform_config.setter
    def platform_config(self, platform_config):
        self._platform_config = platform_config

    @property
    def storage_config(self):
        """Storage configuration loaded from YAML"""
        return self._storage_config

    @storage_config.setter
    def storage_config(self, storage_config):
        self._storage_config = storage_config


class Runtime(abc.ABC):
    """Runtime environment"""

    TEMPLATES = ['config/runtime', '/etc/kernelci/runtime']

    # pylint: disable=unused-argument
    def __init__(self, config, user=None, token=None):
        """A Runtime object can be used to run jobs in a runtime environment

        *config* is a kernelci.config.runtime.Runtime object
        """
        self._config = config
        self._templates = self.TEMPLATES

    @property
    def config(self):
        """RuntimeConfig object for this Runtime instance"""
        return self._config

    @property
    def templates(self):
        """List of template directories used with this runtime"""
        return self._templates

    def _get_template(self, job_config):
        jinja2_env = Environment(loader=FileSystemLoader(self.templates))
        return jinja2_env.get_template(job_config.template)

    def match(self, filter_data):
        """Apply filters and return True if they match, False otherwise."""
        return self.config.match(filter_data)

    def get_params(self, job, api_config=None):
        """Get job template parameters"""
        params = {
            'api_config_yaml': yaml.dump(api_config or {}),
            'storage_config_yaml': yaml.dump(job.storage_config or {}),
            'name': job.name,
            'node_id': job.node['_id'],
            'revision': job.node['revision'],
            'runtime': self.config.lab_type,
            'runtime_image': job.config.image,
            'tarball_url': job.node['artifacts']['tarball'],
        }
        params.update(job.config.params)
        params.update(job.platform_config.params)
        return params

    @classmethod
    def _get_job_file_name(cls, params):
        """Get the file name where to store the generated job definition."""
        return params['name']

    def save_file(self, job, output_path, params, encoding='utf-8'):
        """Save a test job definition in a file.

        *job* is the job definition data
        *output_path* is the directory where the file should be saved
        *params* is a dictionary with template parameters

        Return the full path where the job definition file was saved.
        """
        file_name = self._get_job_file_name(params)
        output_file = os.path.join(output_path, file_name)
        with open(output_file, 'w', encoding=encoding) as output:
            output.write(job)
        return output_file

    @abc.abstractmethod
    def generate(self, job, params):
        """Generate a test job definition.

        *job* is a Job object for the target job
        *params* is a dictionary with the test parameters which can be used
             when generating a job definition using templates
        """

    @abc.abstractmethod
    def submit(self, job_path):
        """Submit a test job definition to run."""

    @abc.abstractmethod
    def get_job_id(self, job_object):
        """Get an id for a given job object as returned by submit()."""


def get_runtime(config, user=None, token=None):
    """Get the Runtime object for a given runtime config.

    *config* is a kernelci.config.runtime.Runtime object
    *user* is the name of the user to connect to the runtime
    *token* is the associated token to connect to the runtime
    """
    module_name = '.'.join(['kernelci', 'runtime', config.lab_type])
    runtime_module = importlib.import_module(module_name)
    return runtime_module.get_runtime(config, user=user, token=token)
