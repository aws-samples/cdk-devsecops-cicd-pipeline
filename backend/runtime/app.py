"""
 Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 SPDX-License-Identifier: MIT-0
"""
from flask import Flask
from flask import request

app = Flask(__name__)

@app.route('/')
def index():
    return '<h1>Hello from Flask & Docker</h2>'

if __name__ == "__main__":
    app.run()