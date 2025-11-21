import React, { useState } from "react";
import { SafeAreaView, View, Text, TextInput, TouchableOpacity, ActivityIndicator, StyleSheet, ScrollView } from "react-native";
import { sendChatMessage } from "../config/api";

export default function ChatScreen() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [response, setResponse] = useState("");

  const handleSend = async () => {
    if (!input.trim()) return;
    setLoading(true);
    setError(null);
    setResponse("");
    try {
      const data = await sendChatMessage(input.trim());
      setResponse(data?.message ?? JSON.stringify(data));
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.inner}>
        <Text style={styles.title}>Chat</Text>
        <Text style={styles.subtitle}>Talk to FloatChat using your existing backend.</Text>

        <View style={styles.chatBox}>
          <ScrollView contentContainerStyle={styles.chatContent}>
            {loading && <ActivityIndicator />}
            {error && <Text style={styles.error}>Error: {error}</Text>}
            {!!response && <Text style={styles.answer}>{response}</Text>}
          </ScrollView>
        </View>

        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            placeholder="Ask a question about the floats..."
            placeholderTextColor="#718096"
            value={input}
            onChangeText={setInput}
            multiline
          />
          <TouchableOpacity style={styles.sendButton} onPress={handleSend} disabled={loading}>
            <Text style={styles.sendText}>{loading ? "..." : "Send"}</Text>
          </TouchableOpacity>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0b1020",
  },
  inner: {
    flex: 1,
    padding: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: "700",
    color: "#fff",
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 13,
    color: "#a0aec0",
    marginBottom: 16,
  },
  chatBox: {
    flex: 1,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#2d3748",
    padding: 12,
    marginBottom: 12,
  },
  chatContent: {
    flexGrow: 1,
  },
  answer: {
    color: "#e2e8f0",
    fontSize: 14,
  },
  error: {
    color: "#fc8181",
    fontSize: 14,
  },
  inputRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 8,
  },
  input: {
    flex: 1,
    minHeight: 40,
    maxHeight: 120,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#2d3748",
    paddingHorizontal: 12,
    paddingVertical: 8,
    color: "#edf2f7",
    fontSize: 14,
  },
  sendButton: {
    backgroundColor: "#3182ce",
    borderRadius: 999,
    paddingHorizontal: 16,
    paddingVertical: 10,
    justifyContent: "center",
    alignItems: "center",
  },
  sendText: {
    color: "#fff",
    fontWeight: "600",
  },
});
