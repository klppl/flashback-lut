# Flashback app static analysis (v1.28.0 build 248)

Source: Mac App Store copy at /Applications/Flashback.app/Wrapper/Flashback.app
Copied: app/main.jsbundle (Hermes bytecode v98), app/Info.plist
Tools: .venv/bin/hbc-decompiler (hermes-dec 0.1.8) -> out/decompiled.js, out/strings.txt (string table)

## Framework
React Native / Expo (SDK 54), Hermes. react-native-ble-plx for BLE. Main Mach-O is FairPlay-encrypted; JS bundle is not.

## Camera
- Models in app: ONE35, ONE35 V2 (BLE name "Flashback-ONE35V2"), ONE75. Name prefixes: Flashback-ONE35, Flashback-ONE35V2, Flashback-ONE75, QC35Flashback.
- USB-C: V2 shows as a file-browser device, folder "ONE35 V2" (app imports roll from it).
- Wi-Fi: "Connect your phone to the camera's temporary network" (camera AP; app has HotspotConfiguration entitlement). Also a "Device Hotspot mode" and a "choose a different connection mode" option.
- Camera HTTP API (relative paths, over the Wi-Fi link):
  - GET/PUT /params   (camera settings, JSON)
  - PUT /roll         (load roll, JSON body)
  - GET /media/<id>   (image download, with retry + header validation)
  - GET /meta/<id>    (image metadata)
  - /files/<...>      (V2 file API; listing root can return 500)
- Feature flags (V2): MEDIAAPI_V2, ADVERTISE_FIRMWARE_VERSION, IS_WOUND, SELFTIMER_SHUTTER, SYSTEM_RTC, CHECK_HEADER, UNLOCK_ON_RESET_KEY.
  GET_PARAMS_BY_BLE is false/null for V2 (V1 may read params over BLE).
- App scans BLE with startDeviceScan(null, allowDuplicates) -> no service UUID filter; filters on name.
- Camera wakes by moving the winder. Rolls are locked to the loading account.
- Firmware blobs bundled: assets/firmware-one35v2 (+beta), one35.

## Not yet found
- BLE service/characteristic UUIDs (not literal strings; built at runtime)
- Camera IP / host address and port
- Wi-Fi SSID/password scheme
- Shutter command (probably BLE)

## Photo character (web research, Nov 2026)
- 13 MP sensor, small; reviews describe stylized, nostalgic, somewhat idealized 90s look; exposure can run bright/washed out.
- "Negatives" export is flat/unprocessed JPEG (no profile); DNG also offered but compatibility reports are mixed.
- Built-in film types: Classic (natural, golden), Mono (crunchy B&W), Beta (magenta-leaning vintage), Cine.
- Implication for LUT design: protect highlights (soft shoulder), don't lift noisy shadows too far, keep skin tones safe.
