#!/usr/bin/env bash
set -euo pipefail
mobile_root="$(cd "$(dirname "$0")/.." && pwd)"
: "${ANDROID_HOME:?Set ANDROID_HOME to your Android SDK}"
"$mobile_root/android/gradlew" -p "$mobile_root/android" :app:assembleDebug "$@"
mkdir -p "$mobile_root/artifacts"
cp "$mobile_root/android/app/build/outputs/apk/debug/app-debug.apk" "$mobile_root/artifacts/defense-arena-debug.apk"
