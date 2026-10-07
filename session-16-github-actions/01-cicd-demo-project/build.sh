#!/bin/bash
# Build step: package the app source into build/ with a small build-info file.
# The CI pipeline uploads build/ as an artifact.
set -e

echo "================================="
echo "Starting Application Build"
echo "================================="

rm -rf build
mkdir -p build

# byte-compile check - fails the build if there is a syntax error
python3 -m compileall -q app

cp -r app requirements.txt build/
rm -rf build/app/__pycache__

cat > build/build-info.txt <<INFO
Application: Session 16 CI/CD Demo
Commit: ${GITHUB_SHA:-local}
Run number: ${GITHUB_RUN_NUMBER:-local}
Build Date: $(date -u)
Build Status: SUCCESS
INFO

tar -czf build/app-build.tar.gz -C build app requirements.txt build-info.txt

echo ""
echo "Build files:"
ls -la build
echo ""
echo "Build completed successfully."
