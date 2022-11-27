#!/usr/bin/env python3

"""
 Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 SPDX-License-Identifier: MIT-0
"""
import aws_cdk as cdk

from pipeline import DevSecOpsPipelineStack
from shared.shared_infra import SharedInfraStack
from sectools.infrastructure import SecTools

import constants

app = cdk.App()

shared_infra = SharedInfraStack(
    app,
    'SharedInfraStack',
    env=constants.DEV_ENV
)

DevSecOpsPipelineStack(
    app,
    "DevSecOpsPipelineStack",
    env=constants.DEV_ENV
)

SecTools(
    app,
    "SecToolsStack",
    env=constants.DEV_ENV
)
app.synth()
