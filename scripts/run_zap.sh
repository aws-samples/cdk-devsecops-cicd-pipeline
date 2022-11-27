#!/bin/bash

##Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
##SPDX-License-Identifier: MIT-0

set -o errexit
set -o verbose

mkdir $SECURITY_SCANNING_OUTPUT_DIR

################
# OWASP ZAP
################

echo $APPLICATION_URL_OUTPUT_KEY
application_url=$(aws cloudformation list-exports --query "Exports[?Name=='$APPLICATION_URL_OUTPUT_KEY'].Value" --output text)
docker run -v $(pwd):/zap/wrk/:rw --user root public.ecr.aws/deepfactor/zap2docker-stable:2.10.0-df zap-baseline.py -t $application_url -J $OWASP_ZAP_OUTPUT_FILE || true
echo "OWASP ZAP analysis status is completed..."; 