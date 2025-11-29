/**
 * Ocean Theme System for FloatChat
 * 
 * This file contains the complete design system for the FloatChat mobile app,
 * including color palette, typography, spacing, and animation constants.
 * The theme is inspired by ocean and marine aesthetics.
 */

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

export interface OceanColors {
  // Backgrounds
  deepOcean: string;
  darkOcean: string;
  midOcean: string;
  
  // Accents
  teal: string;
  aqua: string;
  deepBlue: string;
  
  // Text
  lightWave: string;
  foam: string;
  mist: string;
  
  // States
  success: string;
  warning: string;
  error: string;
  info: string;
  
  // Overlays
  drawerOverlay: string;
  modalOverlay: string;
  
  // Borders
  border: string;
  borderLight: string;
}

export interface TypographyStyle {
  fontSize: number;
  fontWeight: '400' | '500' | '600' | '700' | '800';
  color: string;
  letterSpacing?: number;
  lineHeight?: number;
}

export interface Typography {
  heading1: TypographyStyle;
  heading2: TypographyStyle;
  heading3: TypographyStyle;
  body: TypographyStyle;
  bodyLarge: TypographyStyle;
  caption: TypographyStyle;
  button: TypographyStyle;
  label: TypographyStyle;
}

export interface Spacing {
  xs: number;
  sm: number;
  md: number;
  lg: number;
  xl: number;
  xxl: number;
}

export interface BorderRadius {
  sm: number;
  md: number;
  lg: number;
  xl: number;
  full: number;
}

export interface AnimationConfig {
  duration: number;
  easing: 'ease-in' | 'ease-out' | 'ease-in-out' | 'linear';
}

export interface Animations {
  drawerSlide: AnimationConfig;
  messageAppear: AnimationConfig;
  promptFade: AnimationConfig;
  screenTransition: AnimationConfig;
  quickFade: AnimationConfig;
}

export interface Shadows {
  sm: {
    shadowColor: string;
    shadowOffset: { width: number; height: number };
    shadowOpacity: number;
    shadowRadius: number;
    elevation: number;
  };
  md: {
    shadowColor: string;
    shadowOffset: { width: number; height: number };
    shadowOpacity: number;
    shadowRadius: number;
    elevation: number;
  };
  lg: {
    shadowColor: string;
    shadowOffset: { width: number; height: number };
    shadowOpacity: number;
    shadowRadius: number;
    elevation: number;
  };
}

export interface OceanTheme {
  colors: OceanColors;
  typography: Typography;
  spacing: Spacing;
  borderRadius: BorderRadius;
  animations: Animations;
  shadows: Shadows;
}

// ============================================================================
// COLOR PALETTE
// ============================================================================

export const colors: OceanColors = {
  // Backgrounds - Deep ocean blues for immersive experience
  deepOcean: '#0a1628',      // Primary background - deepest ocean
  darkOcean: '#0d1b2a',      // Secondary background - dark water
  midOcean: '#1a202c',       // Card backgrounds - mid-depth water
  
  // Accents - Vibrant ocean colors for interactive elements
  teal: '#14b8a6',           // Primary accent - tropical water
  aqua: '#06b6d4',           // Secondary accent - shallow water
  deepBlue: '#0284c7',       // Interactive elements - deep water
  
  // Text - Light colors for readability on dark backgrounds
  lightWave: '#e0f2fe',      // Primary text - light wave foam
  foam: '#f0f9ff',           // Headings - white foam
  mist: '#a0aec0',           // Secondary text - ocean mist
  
  // States - Semantic colors for feedback
  success: '#10b981',        // Success messages - sea green
  warning: '#f59e0b',        // Warnings - sunset orange
  error: '#ef4444',          // Errors - coral red
  info: '#3b82f6',           // Info - sky blue
  
  // Overlays - Semi-transparent layers
  drawerOverlay: 'rgba(10, 22, 40, 0.95)',
  modalOverlay: 'rgba(10, 22, 40, 0.8)',
  
  // Borders - Subtle separation
  border: '#2d3748',
  borderLight: '#374151',
};

// ============================================================================
// TYPOGRAPHY
// ============================================================================

export const typography: Typography = {
  heading1: {
    fontSize: 28,
    fontWeight: '700',
    color: colors.foam,
    letterSpacing: -0.5,
    lineHeight: 36,
  },
  heading2: {
    fontSize: 24,
    fontWeight: '700',
    color: colors.foam,
    letterSpacing: -0.3,
    lineHeight: 32,
  },
  heading3: {
    fontSize: 20,
    fontWeight: '600',
    color: colors.lightWave,
    letterSpacing: -0.2,
    lineHeight: 28,
  },
  body: {
    fontSize: 16,
    fontWeight: '400',
    color: colors.lightWave,
    lineHeight: 24,
  },
  bodyLarge: {
    fontSize: 18,
    fontWeight: '400',
    color: colors.lightWave,
    lineHeight: 28,
  },
  caption: {
    fontSize: 13,
    fontWeight: '400',
    color: colors.mist,
    lineHeight: 18,
  },
  button: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.foam,
    letterSpacing: 0.3,
  },
  label: {
    fontSize: 14,
    fontWeight: '500',
    color: colors.lightWave,
    lineHeight: 20,
  },
};

// ============================================================================
// SPACING SYSTEM
// ============================================================================

export const spacing: Spacing = {
  xs: 4,    // Extra small - minimal spacing
  sm: 8,    // Small - tight spacing
  md: 16,   // Medium - standard spacing
  lg: 24,   // Large - comfortable spacing
  xl: 32,   // Extra large - generous spacing
  xxl: 48,  // Extra extra large - section spacing
};

// ============================================================================
// BORDER RADIUS
// ============================================================================

export const borderRadius: BorderRadius = {
  sm: 8,    // Small - subtle rounding
  md: 12,   // Medium - standard rounding
  lg: 16,   // Large - prominent rounding
  xl: 20,   // Extra large - very rounded
  full: 9999, // Full - circular
};

// ============================================================================
// ANIMATIONS
// ============================================================================

export const animations: Animations = {
  drawerSlide: {
    duration: 300,
    easing: 'ease-out',
  },
  messageAppear: {
    duration: 200,
    easing: 'ease-in',
  },
  promptFade: {
    duration: 300,
    easing: 'ease-in-out',
  },
  screenTransition: {
    duration: 250,
    easing: 'ease-in-out',
  },
  quickFade: {
    duration: 150,
    easing: 'ease-in-out',
  },
};

// ============================================================================
// SHADOWS
// ============================================================================

export const shadows: Shadows = {
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 2,
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 4,
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
};

// ============================================================================
// COMPLETE THEME OBJECT
// ============================================================================

export const oceanTheme: OceanTheme = {
  colors,
  typography,
  spacing,
  borderRadius,
  animations,
  shadows,
};

// ============================================================================
// COMPONENT-SPECIFIC STYLES
// ============================================================================

/**
 * Pre-defined styles for common components
 */
export const componentStyles = {
  // Drawer styles
  drawer: {
    container: {
      backgroundColor: colors.drawerOverlay,
      width: '80%',
    },
    header: {
      padding: spacing.md,
      borderBottomWidth: 1,
      borderBottomColor: colors.border,
    },
    searchBar: {
      backgroundColor: colors.midOcean,
      borderRadius: borderRadius.md,
      padding: spacing.sm,
      color: colors.lightWave,
      borderWidth: 1,
      borderColor: colors.border,
    },
    newChatButton: {
      backgroundColor: colors.teal,
      borderRadius: borderRadius.md,
      padding: spacing.md,
      marginTop: spacing.sm,
    },
    item: {
      padding: spacing.md,
      borderRadius: borderRadius.sm,
      marginHorizontal: spacing.sm,
      marginVertical: spacing.xs,
    },
    itemActive: {
      backgroundColor: colors.midOcean,
      borderLeftWidth: 3,
      borderLeftColor: colors.teal,
    },
  },
  
  // Chat message styles
  message: {
    userBubble: {
      backgroundColor: colors.deepBlue,
      borderRadius: borderRadius.xl,
      borderBottomRightRadius: 4,
      padding: spacing.md,
      marginLeft: '20%',
      marginBottom: spacing.sm,
    },
    aiBubble: {
      backgroundColor: colors.midOcean,
      borderRadius: borderRadius.xl,
      borderBottomLeftRadius: 4,
      padding: spacing.md,
      marginRight: '20%',
      marginBottom: spacing.sm,
    },
    text: {
      color: colors.lightWave,
      fontSize: 16,
      lineHeight: 24,
    },
    timestamp: {
      color: colors.mist,
      fontSize: 12,
      marginTop: spacing.xs,
    },
  },
  
  // Quick action button styles
  quickAction: {
    container: {
      flexDirection: 'row' as const,
      gap: spacing.sm,
      marginTop: spacing.sm,
      flexWrap: 'wrap' as const,
    },
    button: {
      backgroundColor: colors.deepOcean,
      borderWidth: 1,
      borderColor: colors.teal,
      borderRadius: borderRadius.xl,
      paddingHorizontal: spacing.md,
      paddingVertical: spacing.sm,
      flexDirection: 'row' as const,
      alignItems: 'center' as const,
      gap: spacing.xs,
    },
    text: {
      color: colors.teal,
      fontSize: 14,
      fontWeight: '600' as const,
    },
  },
  
  // Input styles
  input: {
    container: {
      backgroundColor: colors.midOcean,
      borderRadius: borderRadius.lg,
      borderWidth: 1,
      borderColor: colors.border,
      padding: spacing.md,
    },
    focused: {
      borderColor: colors.teal,
    },
    text: {
      color: colors.lightWave,
      fontSize: 16,
    },
    placeholder: {
      color: colors.mist,
    },
  },
  
  // Button styles
  button: {
    primary: {
      backgroundColor: colors.teal,
      borderRadius: borderRadius.md,
      padding: spacing.md,
      alignItems: 'center' as const,
      justifyContent: 'center' as const,
    },
    secondary: {
      backgroundColor: colors.midOcean,
      borderWidth: 1,
      borderColor: colors.teal,
      borderRadius: borderRadius.md,
      padding: spacing.md,
      alignItems: 'center' as const,
      justifyContent: 'center' as const,
    },
    text: {
      color: colors.foam,
      fontSize: 16,
      fontWeight: '600' as const,
    },
    disabled: {
      backgroundColor: colors.border,
      opacity: 0.5,
    },
  },
  
  // Card styles
  card: {
    container: {
      backgroundColor: colors.midOcean,
      borderRadius: borderRadius.lg,
      padding: spacing.md,
      borderWidth: 1,
      borderColor: colors.border,
    },
    elevated: {
      ...shadows.md,
    },
  },
  
  // Header styles
  header: {
    container: {
      backgroundColor: colors.deepOcean,
      borderBottomWidth: 1,
      borderBottomColor: colors.border,
      paddingVertical: spacing.md,
      paddingHorizontal: spacing.md,
    },
    title: {
      color: colors.foam,
      fontSize: 18,
      fontWeight: '600' as const,
    },
  },
};

// Default export
export default oceanTheme;
