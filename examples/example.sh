#!/bin/bash

pex -r requirements.txt -o lambda_function.zip
lambdex build -s example_function.py lambda_function.zip
lambdex test lambda_function.zip <(echo '{"url": "https://github.com/pantsbuild"}')
