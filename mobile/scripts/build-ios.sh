#!/usr/bin/env bash
set -euo pipefail
mobile_root="$(cd "$(dirname "$0")/.." && pwd)"
command -v xcodebuild >/dev/null || { echo 'iOS builds require macOS and Xcode.' >&2; exit 1; }
# Configure your own signing team in ignored ios/local.xcconfig first.
xcodebuild -project "$mobile_root/ios/DefenseArena.xcodeproj" -scheme DefenseArena -configuration Debug -destination 'generic/platform=iOS' -derivedDataPath "$mobile_root/artifacts/ios-derived" build "$@"
