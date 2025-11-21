import React, { useState } from "react";
import { SafeAreaView, View, Text, TouchableOpacity, ActivityIndicator, StyleSheet, FlatList } from "react-native";
import { fetchIndianOceanFloats } from "../config/api";

export default function MapScreen() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [floats, setFloats] = useState([]);

  const handleLoad = async () => {
    setLoading(true);
    setError(null);
    setFloats([]);
    try {
      const data = await fetchIndianOceanFloats();
      setFloats(data?.floats || []);
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.inner}>
        <Text style={styles.title}>Floats</Text>
        <Text style={styles.subtitle}>Indian Ocean floats from /floats/indian-ocean.</Text>

        <TouchableOpacity style={styles.button} onPress={handleLoad} disabled={loading}>
          <Text style={styles.buttonText}>{loading ? "Loading..." : "Load Floats"}</Text>
        </TouchableOpacity>

        {loading && <ActivityIndicator style={styles.loading} />}
        {error && <Text style={styles.error}>Error: {error}</Text>}

        <FlatList
          data={floats}
          keyExtractor={(item, index) => String(item.float_id || index)}
          style={styles.list}
          renderItem={({ item }) => (
            <View style={styles.card}>
              <Text style={styles.cardTitle}>{item.float_id}</Text>
              <Text style={styles.cardText}>Lat: {item.latitude}</Text>
              <Text style={styles.cardText}>Lon: {item.longitude}</Text>
            </View>
          )}
        />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0b1020" },
  inner: { flex: 1, padding: 16 },
  title: { fontSize: 24, fontWeight: "700", color: "#fff", marginBottom: 4 },
  subtitle: { fontSize: 13, color: "#a0aec0", marginBottom: 12 },
  button: {
    backgroundColor: "#805ad5",
    borderRadius: 999,
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginBottom: 8,
  },
  buttonText: { color: "#fff", fontWeight: "600", textAlign: "center" },
  loading: { marginBottom: 8 },
  error: { color: "#fc8181", marginBottom: 8 },
  list: { flex: 1 },
  card: {
    borderRadius: 10,
    borderWidth: 1,
    borderColor: "#2d3748",
    padding: 10,
    marginBottom: 8,
  },
  cardTitle: { color: "#e2e8f0", fontWeight: "600", marginBottom: 4 },
  cardText: { color: "#a0aec0", fontSize: 13 },
});
