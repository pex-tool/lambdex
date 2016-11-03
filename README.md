# lambdex

lambdex turns pex files into aws lambda functions.

[pex](https://github.com/pantsbuild/pex) is a tool that simplifies packaging python environments and is ideally suited
for aws lambda.  lambdex takes pex files and turns them into aws lambda functions, allowing
you to more easily run complex applications in the cloud.

aws lambda documentation and concepts can be found [here](https://aws.amazon.com/lambda/getting-started/).

## using the lambdex cli

The lambdex cli has two subcommands: `build` and `test`.  `build` further has two possible modes of operation: by specifying
an entry point that already exists within the pex file (`-e`) or by specifying an external script and handler to embed within
the pex file (`-s/-H`).

### step 1: package a pex file

First you must package a pex file.  Assuming you already have the `pex` tool
and a requirements.txt, you can simply run

    pex -r requirements.txt -o lambda_function.pex

to produce a pex file containing the requirements.  If you must build a pex
file with platform-specific extensions, see the tips section below for more
information about building Amazon Linux-specific extensions.

### step 2: add lambdex handler

This can be done one of two ways, depending on where your code lives.

If you have a handler function named 'handler' in package
'mymodule.myapp' that is already contained within lambda_function.pex,
then you can simply run

    lambdex build -e mymodule.myapp:handler lambda_function.pex

If you have a script function.py with a lambda handler named `my_handler`, you would instead run

    lambdex build -s function.py -H my_handler lambda_function.pex

This bundles function.py within the pex environment and instructs lambdex to
call the python function `my_handler` when being invoked by AWS.

### step 3 (optional): test your lambdex function

Once you have created a lambdex file, you can test it as if it were being invoked by Amazon using `lambdex test`.
Given a lambdex package `lambda_function.pex`, you can either send it an empty json event using

    lambdex test --empty lambda_function.pex

You can alternately supply a list of files containing json structs e.g.

    lambdex test lambda_function.pex event1.json event2.json ...

### step 4: upload lambda function

You can create/update lambda functions via the AWS Console, or you can do it
via the CLI using `aws lambda create-function` or `aws lambda update-function-code` respectively.

*NOTE*: When creating the function, you must specify the AWS Lambda handler as
`lambdex_handler.handler`.  Via the CLI, this is the `--handler` flag.  This
is the wrapper injected by lambdex that manages invocation of your code.

Do not confuse this with the `-H` option to `lambdex build`.

## tips

### building amazon linux pex files

Most simple dependencies have no platform-specific extensions and thus can be built anywhere.  However there are a number of
popular packages (e.g. numpy, scipy, matplotlib, PIL, ...) that require building C extensions that can prove tricky
to get packaged correctly.

Amazon provides an amazonlinux docker image which can be useful for building platform-specific extensions to run
on AWS Lambda.  See [documentation](http://docs.aws.amazon.com/AmazonECR/latest/userguide/amazon_linux_container_image.html)
for information about that image.

The minimum Dockerfile to produce can environment that can build Amazon Linux-specific pex files can be found [here](https://github.com/wickman/lambdex/blob/master/Dockerfile)
