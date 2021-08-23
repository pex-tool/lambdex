#!/bin/bash

pex -r requirements.txt -o lambda_function.zip
dist/lambdex build -s example_http_function.py -M main.py lambda_function.zip
dist/lambdex test --type gcp-http lambda_function.zip <(echo '{"url": "https://github.com/pantsbuild"}')
