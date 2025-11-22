import React from "react";
import { View, Text, StyleSheet, TouchableOpacity, Modal } from "react-native";
import { oceanTheme } from "@/theme/oceanTheme";
import { useRouter } from "expo-router";
import { Ionicons } from "@expo/vector-icons";

interface SidebarProps {
  visible: boolean;
  onClose: () => void;
}

export default function Sidebar({ visible, onClose }: SidebarProps) {
  const router = useRouter();

  const menuItems = [
    { title: "Home", icon: "home-outline" as const, route: "/(tabs)" },
    {
      title: "Data",
      icon: "bar-chart-outline" as const,
      route: "/(tabs)/data",
    },
    { title: "Floats", icon: "map-outline" as const, route: "/(tabs)/floats" },
  ];

  const handleNavigation = (route: string) => {
    router.push(route as any);
    onClose();
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="fade"
      onRequestClose={onClose}
    >
      <TouchableOpacity
        style={styles.overlay}
        activeOpacity={1}
        onPress={onClose}
      >
        <View style={styles.sidebar}>
          <View style={styles.header}>
            <Text style={styles.headerText}>Menu</Text>
          </View>

          {menuItems.map((item, index) => (
            <TouchableOpacity
              key={index}
              style={styles.menuItem}
              onPress={() => handleNavigation(item.route)}
            >
              <Ionicons
                name={item.icon}
                size={22}
                color={oceanTheme.colors.text.primary}
                style={styles.menuIcon}
              />
              <Text style={styles.menuText}>{item.title}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </TouchableOpacity>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: "rgba(0, 0, 0, 0.5)",
    justifyContent: "flex-start",
  },
  sidebar: {
    width: 280,
    height: "100%",
    backgroundColor: oceanTheme.colors.surface,
    paddingTop: 60,
  },
  header: {
    paddingHorizontal: oceanTheme.spacing.lg,
    paddingVertical: oceanTheme.spacing.md,
    borderBottomWidth: 1,
    borderBottomColor: oceanTheme.colors.button.primary,
  },
  headerText: {
    fontSize: oceanTheme.typography.fontSize.xl,
    fontWeight: "700",
    color: oceanTheme.colors.text.primary,
  },
  menuItem: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: oceanTheme.spacing.lg,
    paddingVertical: oceanTheme.spacing.md,
  },
  menuIcon: {
    marginRight: oceanTheme.spacing.md,
  },
  menuText: {
    fontSize: oceanTheme.typography.fontSize.md,
    color: oceanTheme.colors.text.primary,
  },
});
