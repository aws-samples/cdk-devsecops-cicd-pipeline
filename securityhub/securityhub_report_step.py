"""
 Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 SPDX-License-Identifier: MIT-0
"""

import jsii
import pathlib

from aws_cdk import aws_codepipeline_actions as cpa
from aws_cdk import aws_codepipeline as codepipeline
from aws_cdk import pipelines
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_iam as iam

from constructs import Construct

import constants

@jsii.implements(pipelines.ICodePipelineActionFactory)
class SecurityHubReportStep(pipelines.Step):
    def __init__(self, id_: str, inputs: pipelines.FileSet, **kwargs) -> None:
        super().__init__(id_)

        self.inputs = inputs

    @jsii.member(jsii_name="produceAction")
    def produce_action(
        self, 
        stage: codepipeline.IStage, 
        options: pipelines.ProduceActionOptions,
    ) -> pipelines.CodePipelineActionFactoryResult:

        runtime_asset = str(pathlib.Path(__file__).parent.joinpath("runtime").resolve())
        function = lambda_.Function(options.scope, "InvokeActionFunction",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="invoke_action_function.handler",
            code=lambda_.Code.from_asset(runtime_asset),     
            environment={
                "SECURITY_HUB_PRODUCT_ARN": constants.SECURITY_HUB_PRODUCT_ARN
            }
        )
        function.add_to_role_policy(
            statement=iam.PolicyStatement(
                actions=[
                    'securityhub:BatchImportFindings'
                ],
                resources=[constants.SECURITY_HUB_PRODUCT_ARN],
            )
        )
    
        stage.add_action(
            cpa.LambdaInvokeAction(
                action_name="SecurityHubReport",
                inputs= [options.artifacts.to_code_pipeline(input) for input in self.inputs],
                lambda_=function,
            )
        )

        return pipelines.CodePipelineActionFactoryResult(run_orders_consumed=1)