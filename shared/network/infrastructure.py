"""
 Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 SPDX-License-Identifier: MIT-0
"""
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_ssm as ssm
from constructs import Construct

import constants

class Network(Construct):
  def __init__(self, scope: Construct, id_: str) -> None:
    super().__init__(scope, id_)

    self.vpc = ec2.Vpc(self, 'VPC',
      ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16")
    )

    ssm.StringParameter(self, 'VPCID', 
        parameter_name=constants.CORE_VPC_PARAMETER_NAME, 
        string_value=self.vpc.vpc_id
    )