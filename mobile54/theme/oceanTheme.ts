interface OceanColors {
  primary: string;
  secondary: string;
  background: string;
  surface: string;
  text: {
    primary: string;
    secondary: string;
    tertiary: string;
  };
  accent: {
    blue: string;
    teal: string;
    coral: string;
    purple: string;
  };
  button: {
    primary: string;
    secondary: string;
    tertiary: string;
  };
}

interface Typography {
  fontFamily: {
    regular: string;
    medium: string;
    bold: string;
  };
  fontSize: {
    xs: number;
    sm: number;
    md: number;
    lg: number;
    xl: number;
    xxl: number;
  };
}

interface Spacing {
  xs: number;
  sm: number;
  md: number;
  lg: number;
  xl: number;
  xxl: number;
}

interface BorderRadius {
  sm: number;
  md: number;
  lg: number;
  xl: number;
  full: number;
}

interface Animations {
  duration: {
    fast: number;
    normal: number;
    slow: number;
  };
}

interface Shadows {
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

interface OceanTheme {
  colors: OceanColors;
  typography: Typography;
  spacing: Spacing;
  borderRadius: BorderRadius;
  animations: Animations;
  shadows: Shadows;
}

export const oceanTheme: OceanTheme = {
  colors: {
    primary: '#1e3a5f',
    secondary: '#2d5f8d',
    background: '#0a0e1a',
    surface: '#1a1f2e',
    text: {
      primary: '#ffffff',
      secondary: '#a0aec0',
      tertiary: '#718096',
    },
    accent: {
      blue: '#4a90e2',
      teal: '#38b2ac',
      coral: '#ff6b6b',
      purple: '#5b5fc7',
    },
    button: {
      primary: '#4a5568',
      secondary: '#2d3748',
      tertiary: '#1a202c',
    },
  },
  typography: {
    fontFamily: {
      regular: 'System',
      medium: 'System',
      bold: 'System',
    },
    fontSize: {
      xs: 12,
      sm: 14,
      md: 16,
      lg: 20,
      xl: 24,
      xxl: 32,
    },
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 16,
    xl: 24,
    full: 9999,
  },
  animations: {
    duration: {
      fast: 150,
      normal: 300,
      slow: 500,
    },
  },
  shadows: {
    sm: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.18,
      shadowRadius: 1.0,
      elevation: 1,
    },
    md: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.23,
      shadowRadius: 2.62,
      elevation: 4,
    },
    lg: {
      shadowColor: '#000',
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.3,
      shadowRadius: 4.65,
      elevation: 8,
    },
  },
};

export default oceanTheme; 