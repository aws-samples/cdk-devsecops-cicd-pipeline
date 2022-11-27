"""
 Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 SPDX-License-Identifier: MIT-0
"""
import aws_cdk as cdk

from backend.infrastructure import Backend

class SampleApplicationBackend(cdk.Stage):
  def __init__(self, scope, id_, stage_name: str, **kwargs):
    super().__init__(scope, id_, **kwargs)

    stateless = cdk.Stack(self, "Stateless")

    self.backend = Backend(stateless, 'Backend', stage_name)
