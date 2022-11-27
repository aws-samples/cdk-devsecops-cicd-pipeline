"""
 Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 SPDX-License-Identifier: MIT-0
"""
import aws_cdk as cdk
from aws_cdk import aws_codecommit as codecommit
from aws_cdk import aws_codebuild as codebuild
from aws_cdk import pipelines
from aws_cdk import aws_secretsmanager as secretsmanager
from aws_cdk import aws_iam as iam
from constructs import Construct

from deployment import SampleApplicationBackend
from securityhub.securityhub_report_step import SecurityHubReportStep

import constants

class DevSecOpsPipelineStack(cdk.Stack):

  def __init__(self, scope: Construct, id_: str, **kwargs) -> None:
    super().__init__(scope, id_, **kwargs)

    repository = codecommit.Repository.from_repository_name(self, 
      'CodeCommitRepo', 
      constants.CODECOMMIT_REPOSITORY_NAME
    )
    source = pipelines.CodePipelineSource.code_commit(repository, branch='main')

    sonarqube_secret_arn = cdk.Fn.import_value(constants.SONARQUBE_SECRET_ARN_EXPORT_NAME)
    sonar_secret = secretsmanager.Secret.from_secret_complete_arn(self, 'SonarQubeSecret', 
      sonarqube_secret_arn
    )

    build_spec = codebuild.BuildSpec.from_object(
      {
        "env": {
          "secrets-manager": {
            "LOGIN": f'{sonar_secret.secret_full_arn}:access_token',
            "HOST": f'{sonar_secret.secret_full_arn}:host',
            "PROJECT": f'{sonar_secret.secret_full_arn}:project'
          },
          "variables": {
            "SECURITY_SCANNING_OUTPUT_DIR": constants.SECURITY_SCANNING_RESULT_DIR,
            "SONAR_SCAN_OUTPUT_FILE": constants.SONARQUBE_SCAN_RESULT_OUTPUT_FILE,
            "SONAR_QUALITY_STATUS_OUTPUT_FILE": constants.SONARQUBE_QUALITY_STATUS_OUTPUT_FILE,
            "SONAR_ISSUES_OUTPUT_FILE": constants.SONARQUBE_ISSUES_OUTPUT_FILE,
            "OWASP_DEPENDENCY_CHECK_OUTPUT_FILE": constants.OWASP_DEPENDENCY_CHECK_OUTPUT_FILE,
            "FAIL_BUILD_FOR_SONAR_QUALITY_STATUS": False
          }
        },
        "phases": {
          "install": {
            "runtime-versions": {
              "python": constants.CDK_APP_PYTHON_VERSION
            },
            "commands": [
              "./scripts/install_dependencies.sh",
              "npm install", 
              "pip3 install -r requirements.txt"
            ],
          },
          "build": {
            "commands": [
              "./scripts/run_tests.sh",
              "npx cdk synth"
            ]
          }
        },
        "version": "0.2",
      }
    )

    # Synth CDK application and build artifacts
    synth_action = pipelines.CodeBuildStep(
      'Build',
      input=source,
      partial_build_spec=build_spec,
      commands=[],
      role_policy_statements=[
        iam.PolicyStatement(
          actions=[
            'secretsmanager:DescribeSecret',
            'secretsmanager:GetSecretValue'
          ],
          resources=[sonarqube_secret_arn],
        ),
        iam.PolicyStatement(
          actions=[
            'ssm:GetParameter',
          ],
          resources=[f'arn:aws:ssm:{constants.REGION}:{constants.DEV_ACCOUNT_ID}:parameter{constants.CORE_VPC_PARAMETER_NAME}'],
        ),        
      ],
      build_environment=codebuild.BuildEnvironment(
        privileged=True
      ),
      cache=codebuild.Cache.local(codebuild.LocalCacheMode.DOCKER_LAYER),
    )
    scan_report_output = synth_action.add_output_directory(
      constants.SECURITY_SCANNING_RESULT_DIR
    )

    pipeline = pipelines.CodePipeline(self,
      'Pipeline',
      docker_enabled_for_synth=True,
      synth=synth_action, 
    )

    # Deploy application in dev
    sample_application_backend = SampleApplicationBackend(
      self,
      f'{constants.CDK_APP_NAME}-Dev',
      'dev',
      env=constants.DEV_ENV
    )
    pipeline.add_stage(
      sample_application_backend,
      pre=[
        pipelines.ManualApprovalStep("PromoteToDev")
      ]
    )

    # Scan with OWASP ZAP
    owasp_zap_build_spec = codebuild.BuildSpec.from_object(
      {
        "env": {
          "variables": {
            "SECURITY_SCANNING_OUTPUT_DIR": constants.SECURITY_SCANNING_RESULT_DIR,
            "OWASP_ZAP_OUTPUT_FILE": constants.OWASP_ZAP_OUTPUT_FILE,
            "APPLICATION_URL_OUTPUT_KEY": sample_application_backend.backend.application_url_output_key
          }
        },
        "phases": {
          "build": {
            "commands": [
              "./scripts/run_zap.sh"
            ]
          }
        },
        "version": "0.2",
      }
    )
    owasp_zap_build_step = pipelines.CodeBuildStep(
      'OwaspZap',
      input=source,
      partial_build_spec=owasp_zap_build_spec,
      build_environment=codebuild.BuildEnvironment(
        privileged=True
      ),
      commands=[], 
      role_policy_statements=[
        iam.PolicyStatement(
          actions=[
            'cloudformation:ListExports',
          ],
          resources=['*'],
        )
      ],
      cache=codebuild.Cache.local(codebuild.LocalCacheMode.DOCKER_LAYER),
    )
    zap_scan_report_output = owasp_zap_build_step.add_output_directory(
      constants.SECURITY_SCANNING_RESULT_DIR
    )
    pipeline.add_wave("OWASP-ZAP").add_pre(owasp_zap_build_step)

    # Send report to Security Hub 
    pipeline.add_wave("SecurityHub-Report").add_pre(
      SecurityHubReportStep('SecurityHubReportStep', inputs=[scan_report_output, zap_scan_report_output])
    )
