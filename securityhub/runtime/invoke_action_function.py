"""
 Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 SPDX-License-Identifier: MIT-0
"""

import os
import boto3
import botocore
import zipfile
import tempfile
import traceback
import json

from boto3.session import Session
from datetime import datetime, timezone

code_pipeline = boto3.client('codepipeline')
securityhub = boto3.client('securityhub')

securityhub_product_arn = os.environ['SECURITY_HUB_PRODUCT_ARN']
account_id = boto3.client('sts').get_caller_identity().get('Account')
region = os.environ['AWS_REGION']

def setup_s3_client(job_data):
    key_id = job_data['artifactCredentials']['accessKeyId']
    key_secret = job_data['artifactCredentials']['secretAccessKey']
    session_token = job_data['artifactCredentials']['sessionToken']
    
    session = Session(aws_access_key_id=key_id,
        aws_secret_access_key=key_secret,
        aws_session_token=session_token)
    return session.client('s3', config=botocore.client.Config(signature_version='s3v4'))

def get_scan_results(s3, scan_report_s3_location):
    tmp_file = tempfile.NamedTemporaryFile()
    bucket = scan_report_s3_location['bucketName']
    key = scan_report_s3_location['objectKey']
    
    scan_results = {}

    with tempfile.NamedTemporaryFile() as tmp_file:
        s3.download_file(bucket, key, tmp_file.name)
        with zipfile.ZipFile(tmp_file.name, 'r') as zip:
            for filename in zip.namelist():
                scan_results[filename] = zip.read(filename).decode('utf-8')

    return scan_results

def process_zap_message(zap_message, job_id):
    finding_type = "Dynamic Code Analysis/Zed Attack Proxy"
    created_at = datetime.now(timezone.utc).isoformat()

    findings = []

    for site in zap_message['site']:
        source_url = site['@name']

        for alert in site['alerts']:
            report_severity = alert['riskcode']
            if report_severity == '2':
                normalized_severity = 50
            elif report_severity == '3':
                normalized_severity = 90
            else:
                normalized_severity= 20

            findings.append(build_security_hub_finding(
                account_id=account_id,
                region=region,
                generator_id=f"codepipeline-{job_id}-zap-alert-{alert['alertRef']}",
                finding_id=alert['alertRef'],
                finding_type=finding_type,
                created_at=created_at,
                finding_title=f"CodePipeline/ZapAnalysis/Alert/{alert['alert']}",
                finding_description=alert['desc'],
                normalized_severity=normalized_severity,
                source_url=source_url,
                job_id=job_id
            ))

    return findings

def process_dependency_check_message(dependency_check_message, job_id):
    finding_type = "Software Composition Analysis/DependencyCheck"
    created_at = datetime.now(timezone.utc).isoformat()

    findings = []

    for dependency in dependency_check_message["dependencies"]:
        if "vulnerabilities" in dependency:
            vulnerability = dependency["vulnerabilities"][0]
            if vulnerability['severity'] == "CRITICAL":
                normalized_severity = 90
            elif vulnerability['severity'] == "HIGH":
                normalized_severity = 70
            else:
                normalized_severity = 50
            finding_description = f"{vulnerability['name']}: Package {dependency['packages'][0]['id']}. Vulnerability ID: {dependency['vulnerabilityIds'][0]['id']}"
            findings.append(build_security_hub_finding(
                account_id=account_id,
                region=region,
                generator_id=f"codepipeline-{job_id}-dependency-check-vulnerability-{dependency['packages'][0]['id']}",
                finding_id=dependency['packages'][0]['id'],
                finding_type=finding_type,
                created_at=created_at,
                finding_title=f"CodePipeline/DependencyCheckAnalysis/Vulnerability/{vulnerability['name']}",
                finding_description=finding_description,
                normalized_severity=normalized_severity,
                source_url=dependency['packages'][0]['url'],
                job_id=job_id
            ))

    return findings

def process_sonar_message(sonar_message, job_id):
    finding_type = "Static Code Analysis/SonarQube"
    created_at = datetime.now(timezone.utc).isoformat()

    sonar_findings = []

    for issue in filter(lambda issue: issue['type'] == 'VULNERABILITY', sonar_message['issues']):
        finding_id = f"{issue['hash']}-sonarqube-codepipeline-{job_id}"
        finding_description = f"{issue['type']}: {issue['message']}. Component: {issue['component']}. Issue ID: {issue['hash']}"
        report_severity = issue['severity']
        if report_severity == 'MAJOR':
            normalized_severity = 70
        elif report_severity == 'BLOCKER':
            normalized_severity = 90
        elif report_severity == 'CRITICAL':
            normalized_severity = 90
        else:
            normalized_severity= 20
        
        sonar_findings.append(build_security_hub_finding(
            account_id=account_id,
            region=region,
            generator_id=f"codepipeline-{job_id}-sonarqube-issue-{issue['hash']}",
            finding_id=finding_id,
            finding_type=finding_type,
            created_at=created_at,
            finding_title=f"CodePipeline/SonarQubeCodeAnalysis/Issue/{issue['hash']}",
            finding_description=finding_description,
            normalized_severity=normalized_severity,
            source_url='',
            job_id=job_id
        ))

    return sonar_findings

def build_security_hub_finding(
    account_id,
    region,
    generator_id,
    finding_id,
    finding_type,
    created_at,
    finding_title,
    finding_description,
    normalized_severity,
    source_url,
    job_id
):
    payload = {
        "SchemaVersion": "2018-10-08",
        "Id": finding_id,
        "ProductArn": securityhub_product_arn,
        "GeneratorId": generator_id,
        "AwsAccountId": account_id,
        "Types": [
            finding_type
        ],
        "CreatedAt": created_at,
        "UpdatedAt": created_at,
        "Severity": {
            "Normalized": normalized_severity,
        },
        "Title":  finding_title,
        "Description": finding_description,
        'Resources': [
            {
                'Id': job_id,
                'Type': "CodePipeline",
                'Partition': "aws",
                'Region': region
            }
        ],
    }

    if source_url:
        payload['SourceUrl'] = source_url

    return payload

def handler(event, context):

    try:
        job_id = event['CodePipeline.job']['id']
        job_data = event['CodePipeline.job']['data']
        artifacts = job_data['inputArtifacts']

        s3 = setup_s3_client(job_data)
        
        securityhub_findings = []

        for artifact in artifacts:

            scan_report_s3_location = artifact['location']['s3Location']

            scan_results = get_scan_results(s3, scan_report_s3_location)

            if "sonar_issues.json" in scan_results:
                securityhub_findings.extend(
                    process_sonar_message(
                        json.loads(scan_results['sonar_issues.json']), 
                        job_id
                    )
                )
            
            if "owasp_dependency_check_result.json" in scan_results:
                securityhub_findings.extend(
                    process_dependency_check_message(
                        json.loads(scan_results['owasp_dependency_check_result.json']),
                        job_id
                    )
                )
                
            if "owasp_zap_result.json" in scan_results:
                securityhub_findings.extend(
                    process_zap_message(
                        json.loads(scan_results['owasp_zap_result.json']),
                        job_id
                    )
                )

        response = securityhub.batch_import_findings(Findings=securityhub_findings)
        if response['FailedCount'] > 0:
            raise Exception("Failed to import finding: {}".format(response['FailedCount']))

        code_pipeline.put_job_success_result(jobId=job_id)

    except Exception as e:
        traceback.print_exc()
        code_pipeline.put_job_failure_result(
            jobId=job_id, 
            failureDetails={
                'message': 'Function exception: ' + str(e), 
                'type': 'JobFailed'
            }
        )

    return "Complete."
