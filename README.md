# id2url


https://github.com/user-attachments/assets/2eb2aa27-2a54-4ef0-9147-86b140cf0d58

Convert package registry coordinates (origin IDs) to source download URLs.

**All registries automatically verify that packages exist** before returning URLs. If a package is not found, a clear error message shows which registries were checked.

## Supported Package Managers

| Registry | Language/Platform | Origin ID Format |
|----------|------------------|------------------|
| **npm** | JavaScript/Node.js | `package/version` or `@scope/package/version` |
| **dart** | Dart/Flutter | `package/version` |
| **pypi** | Python | `package/version` |
| **maven** | Java/JVM + Android | `groupId:artifactId:version` |
| **crates** | Rust | `crate/version` |
| **nuget** | .NET/C# | `package/version` |
| **rubygems** | Ruby | `gem/version` |
| **go** | Go | `module/path/vX.Y.Z` |
| **packagist** | PHP/Composer | `vendor/package/version` |
| **cocoapods** | iOS/macOS | `pod/version` |
| **hex** | Erlang/Elixir | `package/version` |

## Installation

```bash
# Using uv
uv pip install id2url

# Using pip
pip install id2url
```

## CLI Usage

### NPM (JavaScript/Node.js)

```bash
# Regular package
id2url convert npm lodash/4.17.21
# Output: https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz

# Scoped package
id2url convert npm @babel/core/7.22.0
# Output: https://registry.npmjs.org/@babel/core/-/core-7.22.0.tgz

# Non-existent package shows error
id2url convert npm nonexistent-pkg/1.0.0
# Error: Package not found in NPM registry: nonexistent-pkg/1.0.0
```

### Dart (pub.dev)

```bash
id2url convert dart flutter_bloc/8.1.3
# Output: https://pub.dev/api/archives/flutter_bloc-8.1.3.tar.gz

id2url convert dart vm_service/15.0.2
# Output: https://pub.dev/api/archives/vm_service-15.0.2.tar.gz
```

### PyPI (Python)

```bash
id2url convert pypi requests/2.31.0
# Output: https://files.pythonhosted.org/packages/.../requests-2.31.0.tar.gz

# Handles name normalization (underscores, dots, case)
id2url convert pypi typing_extensions/4.8.0
id2url convert pypi Pillow/10.1.0
```

### Maven (Java/JVM + Android)

Maven automatically checks both **Maven Central** and **Google Maven** repositories:

```bash
# Standard Maven Central package
id2url convert maven "com.google.guava:guava:31.1-jre"
# Output: https://repo1.maven.org/maven2/com/google/guava/guava/31.1-jre/guava-31.1-jre-sources.jar

# AndroidX package (found on Google Maven)
id2url convert maven "androidx.glance.wear:wear:1.0.0-alpha10"
# Output: https://dl.google.com/android/maven2/androidx/glance/wear/wear/1.0.0-alpha10/wear-1.0.0-alpha10-sources.jar

# Firebase package
id2url convert maven "com.google.firebase:firebase-analytics:21.5.0"

# 4-part coordinate with packaging
id2url convert maven "com.google.guava:guava:pom:31.1-jre"

# 5-part coordinate with classifier
id2url convert maven "org.lwjgl:lwjgl:jar:3.3.3:natives-windows"

# Non-existent package shows all checked repositories
id2url convert maven "com.nonexistent:package:1.0.0"
# Error: Artifact not found in any Maven repository for com.nonexistent:package:1.0.0
# Checked:
#   - Maven Central: https://repo1.maven.org/maven2/...
#   - Google Maven: https://dl.google.com/android/maven2/...
```

### Crates.io (Rust)

```bash
id2url convert crates serde/1.0.188
# Output: https://static.crates.io/crates/serde/serde-1.0.188.crate

id2url convert crates tokio/1.32.0
# Output: https://static.crates.io/crates/tokio/tokio-1.32.0.crate

id2url convert crates windows-targets/0.52.6
```

### NuGet (.NET/C#)

```bash
id2url convert nuget Newtonsoft.Json/13.0.3
# Output: https://api.nuget.org/v3-flatcontainer/newtonsoft.json/13.0.3/newtonsoft.json.13.0.3.nupkg

id2url convert nuget Microsoft.Extensions.Logging/8.0.0
```

### RubyGems (Ruby)

```bash
# Standard gem
id2url convert rubygems rails/7.1.2
# Output: https://rubygems.org/downloads/rails-7.1.2.gem

# Platform-specific precompiled gem
id2url convert rubygems nokogiri/1.15.4-x86_64-linux
# Output: https://rubygems.org/downloads/nokogiri-1.15.4-x86_64-linux.gem

id2url convert rubygems bundler/2.4.22
```

### Go Modules

```bash
id2url convert go github.com/gin-gonic/gin/v1.9.1
# Output: https://proxy.golang.org/github.com/gin-gonic/gin/@v/v1.9.1.zip

id2url convert go golang.org/x/text/v0.14.0
# Output: https://proxy.golang.org/golang.org/x/text/@v/v0.14.0.zip
```

### Packagist (PHP/Composer)

```bash
id2url convert packagist laravel/framework/v10.35.0
# Output: https://api.github.com/repos/laravel/framework/zipball/v10.35.0

id2url convert packagist monolog/monolog/3.5.0
```

### CocoaPods (iOS/macOS)

```bash
id2url convert cocoapods Alamofire/5.8.1
# Output: https://github.com/Alamofire/Alamofire/archive/5.8.1.tar.gz

id2url convert cocoapods SDWebImage/5.18.5
```

### Hex (Erlang/Elixir)

```bash
# Public package
id2url convert hex phoenix/1.7.10
# Output: https://repo.hex.pm/tarballs/phoenix-1.7.10.tar

id2url convert hex ecto/3.11.0

# Organization package (requires auth)
id2url convert hex @myorg/private_lib/2.0.0
# Output: https://repo.hex.pm/repos/myorg/tarballs/private_lib-2.0.0.tar
```

### Output Formats

```bash
# URL only (default)
id2url convert npm lodash/4.17.21

# JSON output
id2url convert npm lodash/4.17.21 --format json

# TSV output
id2url convert npm lodash/4.17.21 --format tsv
```

### Batch Processing

```bash
# Create input file (TSV or space-separated)
cat > packages.txt << EOF
npm    lodash/4.17.21
pypi   requests/2.31.0
maven  com.google.guava:guava:31.1-jre
crates serde/1.0.188
nuget  Newtonsoft.Json/13.0.3
EOF

# Process batch to JSON
id2url batch packages.txt --format json -o results.json

# Get URLs only
id2url batch packages.txt --format urls

# Continue on errors
id2url batch packages.txt --continue-on-error
```

### List Supported Registries

```bash
id2url list
```

## Python API Usage

```python
from id2url import get_download_url

# Unified API - automatically verifies package exists
name, version, url = get_download_url("npm", "lodash/4.17.21")
print(url)  # https://registry.npmjs.org/lodash/-/lodash-4.17.21.tgz

# Maven - automatically checks Maven Central and Google Maven
name, version, url = get_download_url("maven", "androidx.glance.wear:wear:1.0.0-alpha10")
print(url)  # https://dl.google.com/android/maven2/...

# Handles errors gracefully
try:
    get_download_url("npm", "nonexistent-pkg/1.0.0")
except ValueError as e:
    print(f"Not found: {e}")

# Registry-specific functions
from id2url import get_npm_download_url, get_maven_download_url

name, version, url = get_npm_download_url("@babel/core/7.22.0")
name, version, url = get_maven_download_url("com.google.guava:guava:31.1-jre")
```

## Development

```bash
# Install with dev dependencies
uv sync --extra dev

# Run tests
uv run pytest

# Run linter
uv run ruff check src/

# Format code
uv run ruff format src/
```

## License

Copyright © 2026 Dinesh Ravi

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

See [LICENSE.md](LICENSE.md) for details.
