"""
 Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
 SPDX-License-Identifier: MIT-0
"""
from cryptography.fernet import Fernet

def encrypt():
    key = Fernet.generate_key()
    f = Fernet(key)
    f.encrypt(b"a secret message")
