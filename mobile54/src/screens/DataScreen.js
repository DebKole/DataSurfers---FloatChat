import React, { useState } from "react";
import { SafeAreaView, View, Text, TextInput, TouchableOpacity, ActivityIndicator, StyleSheet, FlatList } from "react-native";
import { fetchTsCurve } from "../config/api";

export default function DataScreen() {
  const [floatId, setFloatId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [measurements, setMeasurements] = useState([]);

  const handleFetch = async () => {
    if (!floatId.trim()) return;
    setLoading(true);
    setError(null);
    setMeasurements([]);
    try {
      const data = await fetchTsCurve(floatId.trim());
      // /api/ts_curve returns { profiles: [ { profileId, measurements: [...] } ] }
      const firstProfile = data?.profiles?.[0];
      setMeasurements(firstProfile?.measurements || []);
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.inner}>
        <Text style={styles.title}>Data</Text>
        <Text style={styles.subtitle}>Fetch T–S profiles for a float using /api/ts_curve.</Text>

        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            placeholder="Enter float_id (e.g. 1901717)"
            placeholderTextColor="#718096"
            value={floatId}
            onChangeText={setFloatId}
          />
          <TouchableOpacity style={styles.button} onPress={handleFetch} disabled={loading}>
            <Text style={styles.buttonText}>{loading ? "..." : "Fetch"}</Text>
          </TouchableOpacity>
        </View>

        {loading && <ActivityIndicator style={styles.loading} />}
        {error && <Text style={styles.error}>Error: {error}</Text>}

        <FlatList
          data={measurements}
          keyExtractor={(_, index) => String(index)}
          style={styles.list}
          renderItem={({ item, index }) => (
            <View style={styles.card}>
              <Text style={styles.cardTitle}>Point {index + 1}</Text>
              <Text style={styles.cardText}>Temp: {item.temperature}</Text>
              <Text style={styles.cardText}>Salinity: {item.salinity}</Text>
            </View>
          )}
        />
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
    marginBottom: 12,
  },
  inputRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 8,
    marginBottom: 12,
  },
  input: {
    flex: 1,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#2d3748",
    paddingHorizontal: 12,
    paddingVertical: 8,
    color: "#edf2f7",
    fontSize: 14,
  },
  button: {
    backgroundColor: "#38a169",
    borderRadius: 999,
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  buttonText: {
    color: "#fff",
    fontWeight: "600",
  },
  loading: {
    marginBottom: 8,
  },
  error: {
    color: "#fc8181",
    marginBottom: 8,
  },
  list: {
    flex: 1,
  },
  card: {
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#2d3748",
    padding: 10,
    marginBottom: 8,
  },
  cardTitle: {
    color: "#e2e8f0",
    fontWeight: "600",
    marginBottom: 4,
  },
  cardText: {
    color: "#a0aec0",
    fontSize: 13,
  },
});
