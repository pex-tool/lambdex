# Release Notes

## 0.1.9

This release fixes a bug wherein, when using the -o/--output option Lambdex would fail to write the
output file if the original input file was not writeable.

## 0.1.8

This release adds an -o/--output option, for when the input file can't be modified.

* An option to write the result to a new file. (#28)

## 0.1.7

This release brings official support for Python 3.10 and 3.11.

## 0.1.6

This release brings support for creating a lambdex that works on GCP. The feature should work for
ancient Pex but is only tested against modern Pex (>=1.6).

* Allow arbitrary handlers to support more runtimes. (#22)
* Create arg that can specify module name. (#21)

## 0.1.5

This release adds support for customizing the entry point at runtime using `LAMBDEX_ENTRY_POINT`

* Use `LAMBDEX_ENTRY_POINT` env var for entry point if available (#19)

## 0.1.4

This release fixes the implicit Lambdex dependency on setuptools and uses the vendored version
supplied by modern versions of Pex.

* Grab setuptools from pex >= 1.6.0. (#8)
