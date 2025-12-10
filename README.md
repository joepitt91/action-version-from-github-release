<!--
SPDX-FileCopyrightText: 2025 Joe Pitt

SPDX-License-Identifier: GPL-3.0-only
-->
# GitHub Action - Get Latest Version from GitHub Releases

Get the latest version from the releases in a GitHub repository.

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| token | The token to authenticate to GitHub with. | Yes |  |
| owner | The owner of the source repository. | yes |  |
| repository | The name of the source repository. | Yes |  |
| greater_equal_version | The minimum version to accept, e.g. 2.0.0. | No | None |
| less_than_version | The version to accept versions less than, e.g. 3.0.0. | No | None |

## Outputs

| Output | Description | Example |
|--------|-------------|---------|
| release_tag | The tag associated with the release for the latest version. | v2.5.3 |
| version | The latest version number. | 2.5.3 |

## Example

```yaml
      - name: Get Latest ComfyUI Version
        id: version
        uses: joepitt91/action-version-from-github-release@v2
        with:
          token: ${{ secrets.PACKAGE_READER_PAT }}
          owner: comfyanonymous
          repository: ComfyUI
```
