# Console Warnings Suppression Guide

This document explains how to suppress verbose system warnings in the Xcode console.

## Quick Setup

### Step 1: Configure Xcode Scheme (Most Important)

The most effective way to suppress system warnings is to set an environment variable in your Xcode scheme:

1. In Xcode, go to **Product > Scheme > Edit Scheme...**
2. Select **Run** in the left sidebar
3. Click the **Arguments** tab
4. Under **Environment Variables**, click the **+** button
5. Add:
   - **Name:** `OS_ACTIVITY_MODE`
   - **Value:** `disable`
6. Click **Close**

This suppresses the verbose activity stream logging from the system, which includes:
- `nw_*` network stack warnings
- `HAL*` audio system warnings
- Many other low-level system messages

### Step 2: Verify Suppression is Active

After setting the environment variable:
1. Clean build folder (Cmd+Shift+K)
2. Build and run the app
3. Check the Xcode console - you should see significantly fewer warnings

## Remaining Warnings

Even with `OS_ACTIVITY_MODE=disable`, you may still see some warnings from:

1. **Third-party libraries** (e.g., Supabase) that use their own networking code
   - These are logged by the libraries themselves
   - They're harmless and don't affect functionality

2. **Connection refused errors** (when backend is down)
   - These are legitimate errors and should not be suppressed
   - They indicate actual connection failures

3. **App-level logs** (messages you intentionally log)
   - These should remain visible for debugging

## Network Warnings Explained

The network warnings you might see are harmless:

- **`nw_socket_set_connection_idle failed [42: Protocol not available]`**
  - The network stack tries to set socket options that aren't available on all connection types
  - This is expected behavior and doesn't affect functionality

- **`nw_protocol_socket_set_no_wake_from_sleep failed [22: Invalid argument]`**
  - Similar to above - trying to set a socket option that's not supported
  - Harmless and doesn't affect app behavior

## Audio/HAL Warnings Explained

Audio warnings in the Simulator are normal:

- **HAL (Hardware Abstraction Layer)** warnings occur because the Simulator emulates audio hardware
- **`iOSSimulatorAudioDevice-*: Abandoning I/O cycle because reconfig pending`** - This happens when the audio system reconfigures (e.g., when starting/stopping recording). The Simulator's audio emulation abandons the current I/O cycle to reconfigure. This is expected behavior and harmless.
- These warnings don't appear on real devices
- They don't affect functionality

## Graphics Warnings Explained

Graphics warnings in the Simulator are normal:

- **`IOSurfaceClientSetSurfaceNotify failed e00002c7`** - This is a graphics rendering warning from the iOS Simulator. The Simulator's graphics emulation sometimes fails to notify the graphics system about surface changes. This is a known Simulator limitation and doesn't affect functionality.
- These warnings only appear in the Simulator
- They don't affect functionality or performance

## Production Builds

Note: `OS_ACTIVITY_MODE=disable` is only recommended for development builds. Production builds should keep full logging for debugging production issues.

To conditionally apply this:
- Set it only in the **Run** scheme (for development)
- Don't set it in **Archive** scheme (for production builds)

## Troubleshooting

If warnings still appear after setting `OS_ACTIVITY_MODE=disable`:

1. **Clean build folder** and rebuild
2. **Restart Xcode** to ensure environment variables are loaded
3. **Check scheme selection** - make sure you're using the correct scheme
4. **Verify environment variable** - in the scheme editor, confirm it shows as enabled

Some warnings (especially from third-party libraries) may still appear because they use direct logging mechanisms outside of the OS activity stream.
