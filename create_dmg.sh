#!/bin/bash

# Simple DMG creation script for Song Editor 2
# This script creates a DMG installer using macOS built-in tools

APP_NAME="Song Editor 2"
DMG_NAME="Song_Editor_2_v2.0.0_macOS.dmg"
APP_PATH="dist/${APP_NAME}.app"
DMG_PATH="${DMG_NAME}"

echo "Creating DMG installer for ${APP_NAME}..."

# Check if the app exists
if [ ! -d "$APP_PATH" ]; then
    echo "Error: Application not found at $APP_PATH"
    exit 1
fi

# Create a temporary directory for the DMG contents
TEMP_DIR=$(mktemp -d)
echo "Using temporary directory: $TEMP_DIR"

# Copy the app to the temporary directory
cp -R "$APP_PATH" "$TEMP_DIR/"

# Create a symbolic link to Applications folder
ln -s /Applications "$TEMP_DIR/Applications"

# Create the DMG
echo "Creating DMG file..."
hdiutil create -volname "$APP_NAME" -srcfolder "$TEMP_DIR" -ov -format UDZO "$DMG_PATH"

# Clean up
rm -rf "$TEMP_DIR"

echo "DMG created successfully: $DMG_PATH"
echo "Size: $(du -h "$DMG_PATH" | cut -f1)"
