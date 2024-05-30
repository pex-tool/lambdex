# Migrating to modern Pex

Lambdex used to be needed to produce zip files useable in lambda functions, but with modern Pex,
it no longer is. Starting with Pex version 2.1.98 you only need to include `import __pex__` at the
top of your lambda handler entrypoint module and build the PEX with
`--inherit-path {fallback,prefer}`.

For example, with the following `my_lambda_module.py`:
```python
import __pex__

import hashlib

import requests


def handler(event, context):
    url = event["url"]
    return {
        url: hashlib.sha256(requests.get(url).content).hexdigest(),
        "requests.__file__": requests.__file__,
    }
```

You can create a zip that will work[^1] in the Python 3.12 AWS lambda runtime with:
```
pex \
    --python python3.12 \
    requests \
    --module my_lambda_module \
    --output-file pex_lambda_function.zip \
    --inherit-path=fallback
```

With the zip uploaded and the lambda runtime configured to use the `my_lambda_module.handler`
handler, you can post an event with `{"url": "https://example.org"}` to the handler endpoint
and see a response similar to:
```json
{
  "https://example.org": "ea8fac7c65fb589b0d53560f5251f74f9e9b243478dcb6b3ea79b5e36449c8d9",
  "requests.__file__": "/var/task/.deps/requests-2.32.3-py3-none-any.whl/requests/__init__.py"
}
```

[^1]: In general, you need to either build the PEX in an environment compatible with the Lambda
  deployment environment or else use the the Pex [`--complete-platform`](
  https://docs.pex-tool.org/buildingpex.html#complete-platform) option to properly cross-resolve
  for the deployement environment. This is no different a requirement than existed when using
  Lambdex to transform a PEX into a lambda-compatible zip previously.
