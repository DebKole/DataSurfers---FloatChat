import React, { useRef, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  StatusBar,
  Animated,
} from "react-native";
import { oceanTheme } from "@/theme/oceanTheme";
import { Ionicons } from "@expo/vector-icons";
import ChatScreen from "@/src/screens/ChatScreen";

export default function HomeScreen() {
  const [hideCards, setHideCards] = useState(false);
  const [firstMessage, setFirstMessage] = useState<string | undefined>(
    undefined
  );
  const fadeAnim = useRef(new Animated.Value(1)).current;
  const quickActions = [
    {
      title: "View Active Floats",
      icon: "map-outline" as const,
      color: oceanTheme.colors.accent.teal,
    },
    {
      title: "Explore Ocean Data",
      icon: "bar-chart-outline" as const,
      color: oceanTheme.colors.accent.blue,
    },
    {
      title: "Chat with OceanBot",
      icon: "chatbubbles-outline" as const,
      color: oceanTheme.colors.accent.purple,
    },
    {
      title: "Nearby Sensors",
      icon: "radio-outline" as const,
      color: oceanTheme.colors.accent.coral,
    },
  ];

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" />

      {hideCards ? (
        <ChatScreen
          initialMessage={firstMessage}
          onFirstUserMessage={() => {}}
        />
      ) : (
        <ScrollView
          style={styles.content}
          contentContainerStyle={styles.contentContainer}
        >
          <Animated.View style={{ opacity: fadeAnim }}>
            <Text style={styles.mainTitle}>
              Where do you want to dive today?
            </Text>
            <View style={styles.actionsContainer}>
              {quickActions.map((action, index) => (
                <TouchableOpacity
                  key={index}
                  style={[styles.actionButton, { borderColor: action.color }]}
                >
                  <Ionicons
                    name={action.icon}
                    size={28}
                    color={action.color}
                    style={{ marginBottom: 8 }}
                  />
                  <Text style={styles.actionTitle}>{action.title}</Text>
                </TouchableOpacity>
              ))}
            </View>
            {/* Render chat input panel after cards, so user can start chatting immediately */}
            <View style={{ marginTop: 16 }}>
              <ChatScreen
                variant="embedded"
                initialMessage={undefined}
                onFirstUserMessage={(msg: string) => {
                  Animated.timing(fadeAnim, {
                    toValue: 0,
                    duration: 250,
                    useNativeDriver: true,
                  }).start(() => {
                    setFirstMessage(msg);
                    setHideCards(true);
                  });
                }}
              />
            </View>
          </Animated.View>
        </ScrollView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: oceanTheme.colors.background,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    padding: 24,
    alignItems: "stretch",
  },
  mainTitle: {
    fontSize: 32,
    fontWeight: "600",
    color: oceanTheme.colors.text.primary,
    marginBottom: 32,
    textAlign: "center",
  },
  actionsContainer: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: 16,
    justifyContent: "center",
  },
  actionButton: {
    width: 160,
    height: 110,
    backgroundColor: oceanTheme.colors.surface,
    borderRadius: 16,
    borderWidth: 2,
    padding: 16,
    alignItems: "center",
    justifyContent: "center",
  },
  actionTitle: {
    color: oceanTheme.colors.text.primary,
    fontSize: 14,
    fontWeight: "500",
    textAlign: "center",
  },
});
