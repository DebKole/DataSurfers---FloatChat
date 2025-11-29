/**
 * Theme configuration for FloatChat
 *
 * This file maintains backward compatibility with the original theme system
 * while exporting the new ocean theme as the default.
 *
 * For the complete ocean theme system, see oceanTheme.ts
 */

import { Platform } from "react-native";
import oceanTheme from "../theme/oceanTheme";

// ============================================================================
// LEGACY THEME (Maintained for backward compatibility)
// ============================================================================

const tintColorLight = "#0a7ea4";
const tintColorDark = "#fff";

/**
 * @deprecated Use oceanTheme.colors instead
 * Legacy color system maintained for backward compatibility
 */
export const Colors = {
  light: {
    text: "#11181C",
    background: "#fff",
    tint: tintColorLight,
    icon: "#687076",
    tabIconDefault: "#687076",
    tabIconSelected: tintColorLight,
  },
  dark: {
    text: "#ECEDEE",
    background: "#151718",
    tint: tintColorDark,
    icon: "#9BA1A6",
    tabIconDefault: "#9BA1A6",
    tabIconSelected: tintColorDark,
  },
};

/**
 * Platform-specific font families
 */
export const Fonts = Platform.select({
  ios: {
    /** iOS `UIFontDescriptorSystemDesignDefault` */
    sans: "system-ui",
    /** iOS `UIFontDescriptorSystemDesignSerif` */
    serif: "ui-serif",
    /** iOS `UIFontDescriptorSystemDesignRounded` */
    rounded: "ui-rounded",
    /** iOS `UIFontDescriptorSystemDesignMonospaced` */
    mono: "ui-monospace",
  },
  default: {
    sans: "normal",
    serif: "serif",
    rounded: "normal",
    mono: "monospace",
  },
  web: {
    sans: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    serif: "Georgia, 'Times New Roman', serif",
    rounded:
      "'SF Pro Rounded', 'Hiragino Maru Gothic ProN', Meiryo, 'MS PGothic', sans-serif",
    mono: "SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
  },
});

// ============================================================================
// OCEAN THEME EXPORTS (New default theme)
// ============================================================================

/**
 * The complete ocean theme system for FloatChat
 * This is the primary theme that should be used throughout the app
 */
export const theme = oceanTheme;

/**
 * Export individual theme components for convenience
 */
export const colors = oceanTheme.colors;
export const animations = oceanTheme.animations;
export const shadows = oceanTheme.shadows;

/**
 * Default export is the complete ocean theme
 */
export default oceanTheme;
