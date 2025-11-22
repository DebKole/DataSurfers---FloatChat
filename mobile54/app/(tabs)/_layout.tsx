import { Tabs } from "expo-router";
import React, { useState } from "react";

import { HapticTab } from "@/components/haptic-tab";
import { IconSymbol } from "@/components/ui/icon-symbol";
import { useColorScheme } from "@/hooks/use-color-scheme";
import Sidebar from "@/components/Sidebar";
import oceanTheme from "@/constants/oceanTheme";
import { View, TouchableOpacity, StyleSheet } from "react-native";

export default function TabLayout() {
  const colorScheme = useColorScheme();
  const [sidebarVisible, setSidebarVisible] = useState(false);

  return (
    <>
      <Sidebar
        visible={sidebarVisible}
        onClose={() => setSidebarVisible(false)}
      />
      <Tabs
        screenOptions={{
          tabBarActiveTintColor: oceanTheme.colors.teal,
          headerShown: true,
          headerStyle: { backgroundColor: oceanTheme.colors.darkOcean },
          headerTitleStyle: { color: oceanTheme.colors.foam },
          headerTintColor: oceanTheme.colors.foam,
          tabBarStyle: { display: "none" },
          tabBarButton: HapticTab,
          headerLeft: () => (
            <TouchableOpacity
              style={styles.menuButton}
              onPress={() => setSidebarVisible(true)}
            >
              <View style={styles.hamburgerLine} />
              <View style={styles.hamburgerLine} />
              <View style={styles.hamburgerLine} />
            </TouchableOpacity>
          ),
        }}
      >
        <Tabs.Screen
          name="index"
          options={{
            title: "Home",
            tabBarIcon: ({ color }) => (
              <IconSymbol size={28} name="house.fill" color={color} />
            ),
          }}
        />
        <Tabs.Screen
          name="data"
          options={{
            title: "Data",
            tabBarIcon: ({ color }) => (
              <IconSymbol size={28} name="chart.xyaxis.line" color={color} />
            ),
          }}
        />
        <Tabs.Screen
          name="floats"
          options={{
            title: "Floats",
            tabBarIcon: ({ color }) => (
              <IconSymbol size={28} name="map" color={color} />
            ),
          }}
        />
      </Tabs>
    </>
  );
}

const styles = StyleSheet.create({
  menuButton: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  hamburgerLine: {
    width: 22,
    height: 2,
    backgroundColor: oceanTheme.colors.foam,
    marginVertical: 2,
    borderRadius: 1,
  },
});
