# Release Notes

## 0.1.5

This release adds support for customizing the entry point at runtime using `LAMBDEX_ENTRY_POINT`

* Use `LAMBDEX_ENTRY_POINT` env var for entry point if available (#19)

## 0.1.4

This release fixes the implicit Lambdex dependency on setuptools and uses the vendored version
supplied by modern versions of Pex.

* Grab setuptools from pex >= 1.6.0. (#8)
