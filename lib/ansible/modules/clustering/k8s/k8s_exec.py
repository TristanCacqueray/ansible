#!/usr/bin/python
# -*- coding: utf-8 -*-

# (c) 2019, Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''

module: k8s_exec

short_description: Execute command in Pod

version_added: "2.9"

author: "Tristan de Cacqueray"

description:
  - Use the Kubernetes Python client to execute command on K8s pods.

requirements:
  - "python >= 2.7"
  - "openshift == 0.4.3"
  - "PyYAML >= 3.11"
'''

EXAMPLES = '''
- name: Execute a command
  k8s_exec:
    namespace: myproject
    pod: zuul-scheduler
    command: zuul-scheduler full-reconfigure
'''

RETURN = '''
result:
  description:
  - The command object
  returned: success
  type: complex
  contains:
     stdout:
       description: The command stdout
       type: str
     stdout_lines:
       description: The command stdout
       type: str
     stderr:
       description: The command stderr
       type: str
     stderr_lines:
       description: The command stderr
       type: str
'''

import copy
import shlex
from ansible.module_utils.k8s.common import KubernetesAnsibleModule
from ansible.module_utils.k8s.common import AUTH_ARG_SPEC, COMMON_ARG_SPEC

from kubernetes.client.apis import core_v1_api
from kubernetes.stream import stream


class KubernetesExecCommand(KubernetesAnsibleModule):
    @property
    def argspec(self):
        spec = copy.deepcopy(COMMON_ARG_SPEC)
        spec.update(copy.deepcopy(AUTH_ARG_SPEC))
        for k in ('kind', 'state', 'force', 'resource_definition', 'src'):
            del spec[k]
        spec['pod'] = {'type': 'str'}
        spec['command'] = {'type': 'str'}
        return spec


def main():
    module = KubernetesExecCommand()
    # Load kubernetes.client.Configuration
    module.get_api_client()
    api = core_v1_api.CoreV1Api()
    resp = stream(
        api.connect_get_namespaced_pod_exec,
        module.params["pod"],
        module.params["namespace"],
        command=shlex.split(module.params["command"]),
        stdout=True,
        stderr=True,
        stdin=False,
        tty=False,
        _preload_content=False)
    stdout, stderr = [], []
    while resp.is_open():
        resp.update(timeout=1)
        if resp.peek_stdout():
            stdout.append(resp.read_stdout())
        if resp.peek_stderr():
            stderr.append(resp.read_stderr())
    module.exit_json(
        changed=True, stdout="".join(stdout), stderr="".join(stderr))


if __name__ == '__main__':
    main()
