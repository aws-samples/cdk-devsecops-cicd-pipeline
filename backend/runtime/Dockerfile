# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
FROM public.ecr.aws/docker/library/python:3.9.15-slim

WORKDIR /api

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

ENV FLASK_APP app/app.py

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]