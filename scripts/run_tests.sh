#!/bin/bash

##Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
##SPDX-License-Identifier: MIT-0

set -o errexit
set -o verbose

mkdir $SECURITY_SCANNING_OUTPUT_DIR

################
# SonarQube
################

./sonar-scanner-4.7.0.2747-linux/bin/sonar-scanner -Dsonar.host.url=$HOST -Dsonar.login=$LOGIN -Dsonar.projectKey=$PROJECT -Dsonar.sources=backend/runtime/  > $SONAR_SCAN_OUTPUT_FILE
sonar_task_id=$(cat $SONAR_SCAN_OUTPUT_FILE | egrep -o "task\?id=[^ ]+" | cut -d'=' -f2)
stat="PENDING";
while [ "$stat" != "SUCCESS" ]; do
    if [ $stat = "FAILED" ] || [ $stat = "CANCELLED" ]; then
        echo "SonarQube task $sonar_task_id failed";
        exit 1;
    fi
    stat=$(curl -u $LOGIN: $HOST/api/ce/task\?id=$sonar_task_id | jq -r '.task.status');
    sleep 5;
done

sonar_analysis_id=$(curl -u $LOGIN: $HOST/api/ce/task\?id=$sonar_task_id | jq -r '.task.analysisId')
curl -o $SONAR_QUALITY_STATUS_OUTPUT_FILE -u $LOGIN: $HOST/api/qualitygates/project_status\?analysisId=$sonar_analysis_id
quality_status=$(cat $SONAR_QUALITY_STATUS_OUTPUT_FILE | jq -r '.projectStatus.status')
curl -o $SONAR_ISSUES_OUTPUT_FILE -u $LOGIN: $HOST/api/issues/search?createdAfter=2022-11-10&componentKeys=$PROJECT&severities=CRITICAL,BLOCKER&types=VULNERABILITY&onComponentOnly=true

if [ $FAIL_BUILD_FOR_SONAR_QUALITY_STATUS = true ] ; then
    if [ $quality_status = "ERROR" ] || [ $quality_status = "WARN" ]; then
        echo "in quality_status ERROR or WARN condition"
        exit 1;
    elif [ $quality_status = "OK" ]; then
        echo "in quality_status OK condition"
    else
        echo "in quality_status unexpected condition"
        exit 1;
    fi
fi

########################
# OWASP Dependency-Check
########################
./dependency-check/bin/dependency-check.sh --project $PROJECT --format JSON --prettyPrint --enableExperimental --scan backend/runtime --out $OWASP_DEPENDENCY_CHECK_OUTPUT_FILE
echo "OWASP dependency check analysis status is completed..."; 
