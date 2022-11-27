"""
 Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 SPDX-License-Identifier: MIT-0
"""
import aws_cdk as cdk

CDK_APP_NAME = "SampleDevSecOps-CICD-Pipeline"

CDK_APP_PYTHON_VERSION = "3.7"

DEV_ACCOUNT_ID = "<MY_ACCOUNT_ID>"
REGION = "<MY_REGION>"

DEV_ENV = cdk.Environment(account=DEV_ACCOUNT_ID, region=REGION)

CODECOMMIT_REPOSITORY_NAME = "cdk-devsecops-cicd-pipeline"

CORE_VPC_PARAMETER_NAME = "/SampleDevSecOpsCICDPipeline/CoreVPCID"

SONARQUBE_SECRET_ARN_EXPORT_NAME = "SonarQubeSecretArn"

SONARQUBE_RESULT_REPORT_OUTPUT_NAME = "sonar_result"
SECURITY_SCANNING_RESULT_DIR = "security_scanning_output"
SONARQUBE_SCAN_RESULT_OUTPUT_FILE = f"{SECURITY_SCANNING_RESULT_DIR}/sonarscan_result.txt"
SONARQUBE_QUALITY_STATUS_OUTPUT_FILE = f"{SECURITY_SCANNING_RESULT_DIR}/sonar_quality_status.json"
SONARQUBE_ISSUES_OUTPUT_FILE = f"{SECURITY_SCANNING_RESULT_DIR}/sonar_issues.json"
OWASP_DEPENDENCY_CHECK_OUTPUT_FILE = f"{SECURITY_SCANNING_RESULT_DIR}/owasp_dependency_check_result.json"
OWASP_ZAP_OUTPUT_FILE = f"{SECURITY_SCANNING_RESULT_DIR}/owasp_zap_result.json"

SECURITY_HUB_PRODUCT_ARN = "arn:aws:securityhub:{0}:{1}:product/{1}/default".format(REGION, DEV_ACCOUNT_ID)
