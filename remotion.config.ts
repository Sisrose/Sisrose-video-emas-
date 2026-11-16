import fs from "node:fs";
import { Config } from "@remotion/cli/config";

Config.setVideoImageFormat("jpeg");
Config.setOverwriteOutput(true);
Config.setEntryPoint("src/index.ts");

// Dalam persekitaran awan Claude, guna Chromium yang sudah dipasang.
const chromiumAwan = "/opt/pw-browsers/chromium-1243/chrome-linux64/chrome";
if (fs.existsSync(chromiumAwan)) {
  Config.setBrowserExecutable(chromiumAwan);
}
