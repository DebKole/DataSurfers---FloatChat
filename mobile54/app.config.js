// Loads environment variables from .env at project root (mobile54/.env)
const path = require("path");
const fs = require("fs");
const dotenv = require("dotenv");

// Prefer repo root .env (one level up), fallback to local .env
const rootEnvPath = path.resolve(__dirname, "..", ".env");
const localEnvPath = path.resolve(__dirname, ".env");
if (fs.existsSync(rootEnvPath)) {
  dotenv.config({ path: rootEnvPath });
} else {
  dotenv.config({ path: localEnvPath });
}

/**
 * Expo app config with env-sourced values
 */
module.exports = {
  expo: {
    name: "mobile54",
    slug: "mobile54",
    version: "1.0.0",
    orientation: "portrait",
    icon: "./assets/images/icon.png",
    scheme: "mobile54",
    userInterfaceStyle: "automatic",
    newArchEnabled: true,
    ios: {
      supportsTablet: true,
    },
    android: {
      adaptiveIcon: {
        backgroundColor: "#E6F4FE",
        foregroundImage: "./assets/images/android-icon-foreground.png",
        backgroundImage: "./assets/images/android-icon-background.png",
        monochromeImage: "./assets/images/android-icon-monochrome.png",
        config: {
          googleMaps: {
            apiKey: process.env.GOOGLE_MAPS_API_KEY || "",
          },
        },
      },
      edgeToEdgeEnabled: true,
      softwareKeyboardLayoutMode: "resize",
      predictiveBackGestureEnabled: false,
      package: "com.parv_setia.mobile54",
    },
    web: {
      output: "static",
      favicon: "./assets/images/favicon.png",
    },
    plugins: [
      "expo-router",
      [
        "expo-splash-screen",
        {
          image: "./assets/images/splash-icon.png",
          imageWidth: 200,
          resizeMode: "contain",
          backgroundColor: "#ffffff",
          dark: {
            backgroundColor: "#000000",
          },
        },
      ],
      "expo-maps",
    ],
    experiments: {
      typedRoutes: true,
      reactCompiler: true,
    },
    extra: {
      router: {},
      eas: {
        projectId: "59349a6f-08d6-4989-a9a8-b6a286d1f0d1",
      },
    },
  },
};
