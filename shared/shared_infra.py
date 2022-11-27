"""
 Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 SPDX-License-Identifier: MIT-0
"""
import aws_cdk as cdk
from constructs import Construct

from shared.network.infrastructure import Network

class SharedInfraStack(cdk.Stack):
  def __init__(self, scope: Construct, id_: str, **kwargs) -> None:
    super().__init__(scope, id_, **kwargs)

    self.network = Network(self, "Network")

    cdk.CfnOutput(self, 'CoreVPC', value=self.network.vpc.vpc_id, export_name='CoreVPCId')
