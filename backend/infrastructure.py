"""
 Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 SPDX-License-Identifier: MIT-0
"""
import pathlib

from constructs import Construct
from aws_cdk.aws_ecr_assets import DockerImageAsset

import aws_cdk as cdk
import aws_cdk.aws_ecs as ecs
import aws_cdk.aws_ecs_patterns as ecsp
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_ssm as ssm

import constants

class Backend(Construct):
  def __init__(self, scope: Construct, id_: str, stage_name: str) -> None:
    super().__init__(scope, id_)

    runtime_asset = str(pathlib.Path(__file__).parent.joinpath("runtime").resolve())
    docker_image_asset = DockerImageAsset(self, "SampleApp-API",
        directory=runtime_asset
    )

    vpc = ec2.Vpc.from_lookup(self, "VPC", 
      vpc_id=ssm.StringParameter.value_from_lookup(self, constants.CORE_VPC_PARAMETER_NAME)
    )

    backend_ecs = ecsp.ApplicationLoadBalancedFargateService(self, "BackendAPI",
      task_image_options=ecsp.ApplicationLoadBalancedTaskImageOptions(
        image=ecs.ContainerImage.from_ecr_repository(
          repository=docker_image_asset.repository,
          tag=docker_image_asset.image_tag),
        container_port=5000
      ),
      public_load_balancer=True,
      vpc=vpc
    )

    self.application_url_output_key = f'{constants.CDK_APP_NAME}-{stage_name}'

    cdk.CfnOutput(self, 'SonarQubeSecretArnOutput',
      value=f"http://{backend_ecs.load_balancer.load_balancer_dns_name}",
      export_name=self.application_url_output_key
    )

