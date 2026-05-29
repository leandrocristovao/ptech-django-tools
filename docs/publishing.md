# Publishing

This project uses GitHub Actions and PyPI trusted publishing.

## TestPyPI

Use the workflow named `Publish to TestPyPI` to publish a release candidate or a smoke-test build.

Before the first run, configure a trusted publisher in TestPyPI with:

- repository owner
- repository name
- workflow file: `.github/workflows/publish-testpypi.yml`
- environment: `testpypi`

## PyPI

Use a GitHub Release to publish the final release.

Before the first run, configure a trusted publisher in PyPI with:

- repository owner
- repository name
- workflow file: `.github/workflows/publish-pypi.yml`
- environment: `pypi`

## Release flow

1. Bump the version in `pyproject.toml`.
2. Push the change and let CI pass.
3. Run the TestPyPI workflow if you want a dry run of the release.
4. Create a GitHub Release from the final tag, for example `v0.1.0`.
5. The PyPI workflow will publish the tag after the release is published.

