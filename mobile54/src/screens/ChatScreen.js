import React, { useState, useRef } from "react";
import {
  SafeAreaView,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
  Keyboard,
  LayoutAnimation,
  Dimensions,
} from "react-native";
import { sendChatMessage } from "../config/api";
import { oceanTheme } from "../../constants/oceanTheme";
import { useSafeAreaInsets } from "react-native-safe-area-context";

export default function ChatScreen({
  onFirstUserMessage,
  initialMessage,
  variant = "full",
}) {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const scrollViewRef = useRef(null);
  const didAutoSend = useRef(false);
  const [keyboardOffset, setKeyboardOffset] = useState(0);

  const sendMessage = async (content) => {
    if (!content || loading) return;

    const userMessage = { role: "user", content };
    // Notify parent only on the very first user message
    if (typeof onFirstUserMessage === "function" && messages.length === 0) {
      try {
        onFirstUserMessage(userMessage.content);
      } catch {}
    }
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const data = await sendChatMessage(userMessage.content);
      const aiMessage = {
        role: "assistant",
        content: data?.message ?? JSON.stringify(data),
      };
      setMessages((prev) => [...prev, aiMessage]);
    } catch (e) {
      const errorMessage = {
        role: "assistant",
        content: `Error: ${e.message || String(e)}`,
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      setTimeout(
        () => scrollViewRef.current?.scrollToEnd({ animated: true }),
        100
      );
    }
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    await sendMessage(text);
  };

  // Auto-send initialMessage on mount/switch without relying on input state
  React.useEffect(() => {
    if (
      initialMessage &&
      !didAutoSend.current &&
      messages.length === 0 &&
      !loading
    ) {
      didAutoSend.current = true;
      sendMessage(initialMessage);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialMessage]);

  // Android: track keyboard height and animate layout so input stays visible
  React.useEffect(() => {
    const show = Keyboard.addListener("keyboardDidShow", (e) => {
      if (Platform.OS === "android") {
        const screenH = Dimensions.get("screen").height;
        const fromScreenY = screenH - (e.endCoordinates?.screenY ?? screenH);
        const explicitH = e.endCoordinates?.height ?? 0;
        const offset = Math.max(explicitH, fromScreenY, 0);
        LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
        setKeyboardOffset(offset);
        setTimeout(
          () => scrollViewRef.current?.scrollToEnd({ animated: true }),
          150
        );
      }
    });
    const hide = Keyboard.addListener("keyboardDidHide", () => {
      if (Platform.OS === "android") {
        LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
        setKeyboardOffset(0);
      }
    });
    return () => {
      show.remove();
      hide.remove();
    };
  }, []);

  const isEmbedded = variant === "embedded";
  const isFull = !isEmbedded;
  const [inputBarHeight, setInputBarHeight] = useState(76);
  const insets = useSafeAreaInsets();

  return (
    <SafeAreaView
      style={[styles.container, isEmbedded && styles.containerEmbedded]}
    >
      <KeyboardAvoidingView
        style={[styles.keyboardView, isEmbedded && styles.keyboardViewEmbedded]}
        behavior={
          Platform.OS === "ios" ? "padding" : isEmbedded ? "height" : undefined
        }
        keyboardVerticalOffset={Platform.OS === "ios" ? 90 : isEmbedded ? 0 : 0}
      >
        <ScrollView
          ref={scrollViewRef}
          style={[
            styles.messagesContainer,
            isEmbedded && styles.messagesContainerEmbedded,
          ]}
          contentContainerStyle={[
            styles.messagesContent,
            isEmbedded && styles.messagesContentEmbedded,
            // Pad bottom by measured input height so messages never scroll under the input
            Platform.OS === "android" && isFull
              ? { paddingBottom: inputBarHeight + insets.bottom + 16 }
              : null,
          ]}
          keyboardShouldPersistTaps="handled"
          onContentSizeChange={() =>
            scrollViewRef.current?.scrollToEnd({ animated: true })
          }
        >
          {messages.length === 0 && (
            <View
              style={[
                styles.emptyState,
                isEmbedded && styles.emptyStateEmbedded,
              ]}
            >
              <Text style={styles.emptyText}>
                Ask me anything about ocean floats
              </Text>
            </View>
          )}

          {messages.map((msg, idx) => (
            <View
              key={idx}
              style={[
                styles.messageBubble,
                msg.role === "user" ? styles.userBubble : styles.aiBubble,
              ]}
            >
              <Text
                style={[styles.messageText, msg.isError && styles.errorText]}
              >
                {msg.content}
              </Text>
            </View>
          ))}

          {loading && (
            <View style={styles.aiBubble}>
              <ActivityIndicator color={oceanTheme.colors.teal} />
            </View>
          )}
        </ScrollView>

        {/* Spacer is handled via paddingBottom above when Android full chat */}
      </KeyboardAvoidingView>
      {/* Input bar: outside KAV so Android adjustResize keeps it attached to bottom */}
      <View
        style={[
          styles.inputContainer,
          isEmbedded && styles.inputContainerEmbedded,
          Platform.OS === "android" && isFull
            ? {
                position: "absolute",
                left: 0,
                right: 0,
                bottom: keyboardOffset > 10 ? keyboardOffset : insets.bottom,
                zIndex: 10,
                elevation: 8,
              }
            : null,
        ]}
        onLayout={(e) => {
          const h = e.nativeEvent.layout.height;
          if (h && Math.abs(h - inputBarHeight) > 1) setInputBarHeight(h);
        }}
      >
        <TextInput
          style={[styles.input, isEmbedded && styles.inputEmbedded]}
          placeholder="Message FloatChat..."
          placeholderTextColor={oceanTheme.colors.mist}
          value={input}
          onChangeText={setInput}
          onFocus={() =>
            setTimeout(
              () => scrollViewRef.current?.scrollToEnd({ animated: true }),
              150
            )
          }
          multiline
          maxLength={2000}
        />
        <TouchableOpacity
          style={[
            styles.sendButton,
            (!input.trim() || loading) && styles.sendButtonDisabled,
          ]}
          onPress={handleSend}
          disabled={!input.trim() || loading}
        >
          <Text style={styles.sendText}>↑</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: oceanTheme.colors.deepOcean,
  },
  containerEmbedded: {
    backgroundColor: "transparent",
  },
  keyboardView: {
    flex: 1,
  },
  keyboardViewEmbedded: {
    flex: 0,
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContainerEmbedded: {
    maxHeight: 120,
  },
  messagesContent: {
    padding: 16,
    paddingBottom: 8,
  },
  messagesContentEmbedded: {
    padding: 0,
  },
  emptyState: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingTop: 100,
  },
  emptyStateEmbedded: {
    paddingTop: 0,
  },
  emptyText: {
    color: oceanTheme.colors.mist,
    fontSize: 16,
  },
  messageBubble: {
    maxWidth: "80%",
    padding: 12,
    borderRadius: 16,
    marginBottom: 12,
  },
  userBubble: {
    alignSelf: "flex-end",
    backgroundColor: oceanTheme.colors.deepBlue,
    borderBottomRightRadius: 4,
  },
  aiBubble: {
    alignSelf: "flex-start",
    backgroundColor: oceanTheme.colors.midOcean,
    borderBottomLeftRadius: 4,
  },
  messageText: {
    color: oceanTheme.colors.lightWave,
    fontSize: 16,
    lineHeight: 22,
  },
  errorText: {
    color: oceanTheme.colors.error,
  },
  inputContainer: {
    flexDirection: "row",
    alignItems: "flex-end",
    padding: 16,
    paddingTop: 8,
    backgroundColor: oceanTheme.colors.deepOcean,
    borderTopWidth: 1,
    borderTopColor: oceanTheme.colors.border,
    gap: 8,
  },
  inputContainerEmbedded: {
    backgroundColor: "transparent",
    borderTopWidth: 0,
    padding: 0,
    paddingTop: 8,
  },
  input: {
    flex: 1,
    minHeight: 44,
    maxHeight: 120,
    backgroundColor: oceanTheme.colors.midOcean,
    borderRadius: 22,
    paddingHorizontal: 16,
    paddingVertical: 12,
    color: oceanTheme.colors.lightWave,
    fontSize: 16,
  },
  inputEmbedded: {
    backgroundColor: oceanTheme.colors.midOcean,
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: oceanTheme.colors.teal,
    justifyContent: "center",
    alignItems: "center",
  },
  sendButtonDisabled: {
    backgroundColor: oceanTheme.colors.border,
    opacity: 0.5,
  },
  sendText: {
    color: oceanTheme.colors.foam,
    fontSize: 24,
    fontWeight: "700",
  },
});
