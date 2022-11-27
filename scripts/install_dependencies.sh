#!/bin/bash

##Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
##SPDX-License-Identifier: MIT-0

set -o errexit
set -o verbose

wget https://binaries.sonarsource.com/Distribution/sonar-scanner-cli/sonar-scanner-cli-4.7.0.2747-linux.zip
unzip sonar-scanner-cli-4.7.0.2747-linux.zip

wget https://github.com/jeremylong/DependencyCheck/releases/download/v7.3.0/dependency-check-7.3.0-release.zip
unzip dependency-check-7.3.0-release.zip