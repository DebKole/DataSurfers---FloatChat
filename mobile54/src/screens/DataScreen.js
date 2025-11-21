import React, { useState, useMemo } from "react";
import { SafeAreaView, View, Text, TextInput, TouchableOpacity, ActivityIndicator, StyleSheet, FlatList, Linking } from "react-native";
import { fetchTsCurve, fetchTdCurve, getTsCurvePngUrl, getTdCurvePngUrl, fetchCompareTs, fetchCompareTd, getCompareTsPngUrl, getCompareTdPngUrl } from "../config/api";

export default function DataScreen() {
  const [floatId, setFloatId] = useState("");
  const [floatIdB, setFloatIdB] = useState("");
  const [mode, setMode] = useState("TS");
  const [compare, setCompare] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [measurements, setMeasurements] = useState([]);

  const handleFetch = async () => {
    if (!floatId.trim()) return;
    if (compare && !floatIdB.trim()) return;
    setLoading(true);
    setError(null);
    setMeasurements([]);
    try {
      const id = floatId.trim();
      const idB = floatIdB.trim();
      let data;
      if (compare) {
        data = mode === "TS" ? await fetchCompareTs(id, idB) : await fetchCompareTd(id, idB);
      } else {
        data = mode === "TS" ? await fetchTsCurve(id) : await fetchTdCurve(id);
      }

      const profiles = data?.profiles || [];
      if (!profiles.length) {
        setMeasurements([]);
      } else if (compare) {
        // For compare, flatten first measurement (stats) for each profile
        const combined = [];
        profiles.forEach((p, idx) => {
          const stats = (p.measurements || [])[0] || {};
          combined.push({
            _profileIndex: idx,
            label: p.label || (idx === 0 ? id : idB),
            ...stats,
          });
        });
        setMeasurements(combined);
      } else {
        const firstProfile = profiles[0];
        setMeasurements(firstProfile?.measurements || []);
      }
    } catch (e) {
      setError(e.message || String(e));
    } finally {
      setLoading(false);
    }
  };

  const graphValues = useMemo(() => {
    if (!measurements.length || compare) return [];
    if (mode === "TS") {
      return measurements.map((m) => m.temperature).filter((v) => typeof v === "number");
    }
    return measurements.map((m) => m.temperature).filter((v) => typeof v === "number");
  }, [measurements, mode, compare]);

  const handleDownloadTdPng = async () => {
    if (mode !== "TD" || !floatId.trim()) return;
    try {
      const url = getTdCurvePngUrl(floatId.trim());
      await Linking.openURL(url);
    } catch (e) {
      setError(e.message || String(e));
    }
  };

  const handleDownloadTsPng = async () => {
    if (mode !== "TS" || !floatId.trim()) return;
    try {
      const url = getTsCurvePngUrl(floatId.trim());
      await Linking.openURL(url);
    } catch (e) {
      setError(e.message || String(e));
    }
  };

  const handleDownloadComparePng = async () => {
    if (!compare || !floatId.trim() || !floatIdB.trim()) return;
    try {
      const id = floatId.trim();
      const idB = floatIdB.trim();
      const url = mode === "TS" ? getCompareTsPngUrl(id, idB) : getCompareTdPngUrl(id, idB);
      await Linking.openURL(url);
    } catch (e) {
      setError(e.message || String(e));
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.inner}>
        <Text style={styles.title}>Data</Text>
        <Text style={styles.subtitle}>Fetch T–S and T–D profiles for a float.</Text>

        <View style={styles.modeRow}>
          <TouchableOpacity
            style={[styles.modeButton, mode === "TS" && styles.modeButtonActive]}
            onPress={() => setMode("TS")}
            disabled={loading}
          >
            <Text style={[styles.modeButtonText, mode === "TS" && styles.modeButtonTextActive]}>TS</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.modeButton, mode === "TD" && styles.modeButtonActive]}
            onPress={() => setMode("TD")}
            disabled={loading}
          >
            <Text style={[styles.modeButtonText, mode === "TD" && styles.modeButtonTextActive]}>TD</Text>
          </TouchableOpacity>
        </View>

        <View style={styles.compareRow}>
          <TouchableOpacity
            style={[styles.compareButton, compare && styles.modeButtonActive]}
            onPress={() => setCompare((v) => !v)}
            disabled={loading}
          >
            <Text style={styles.modeButtonText}>{compare ? "Compare: ON" : "Compare: OFF"}</Text>
          </TouchableOpacity>
        </View>

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

        {compare && (
          <View style={styles.inputRow}>
            <TextInput
              style={styles.input}
              placeholder="Enter second float_id"
              placeholderTextColor="#718096"
              value={floatIdB}
              onChangeText={setFloatIdB}
            />
          </View>
        )}

        {mode === "TS" && !!floatId.trim() && !compare && (
          <TouchableOpacity style={[styles.button, { marginBottom: 8 }]} onPress={handleDownloadTsPng} disabled={loading}>
            <Text style={styles.buttonText}>Download TS PNG</Text>
          </TouchableOpacity>
        )}

        {mode === "TD" && !!floatId.trim() && !compare && (
          <TouchableOpacity style={[styles.button, { marginBottom: 8 }]} onPress={handleDownloadTdPng} disabled={loading}>
            <Text style={styles.buttonText}>Download TD PNG</Text>
          </TouchableOpacity>
        )}

        {compare && !!floatId.trim() && !!floatIdB.trim() && (
          <TouchableOpacity style={[styles.button, { marginBottom: 8 }]} onPress={handleDownloadComparePng} disabled={loading}>
            <Text style={styles.buttonText}>Download Compare {mode} PNG</Text>
          </TouchableOpacity>
        )}

        {loading && <ActivityIndicator style={styles.loading} />}
        {error && <Text style={styles.error}>Error: {error}</Text>}
        {!loading && !error && !!floatId.trim() && measurements.length === 0 && (
          <Text style={styles.empty}>
            No data found for {compare ? "these floats" : "this float"} in {mode} mode.
          </Text>
        )}

        {!!graphValues.length && (
          <View style={styles.graphContainer}>
            <Text style={styles.graphTitle}>{mode === "TS" ? "Temperature profile (TS)" : "Temperature profile (TD)"}</Text>
            <View style={styles.graphBarRow}>
              {graphValues.map((v, i) => (
                <View key={i} style={[styles.graphBar, { height: 10 + (i / graphValues.length) * 10 }]} />
              ))}
            </View>
          </View>
        )}

        <FlatList
          data={measurements}
          keyExtractor={(_, index) => String(index)}
          style={styles.list}
          renderItem={({ item, index }) => (
            <View style={styles.card}>
              {compare && (
                <Text style={styles.cardTitle}>Float: {item.label || (index === 0 ? floatId : floatIdB)}</Text>
              )}
              {!compare && <Text style={styles.cardTitle}>Point {index + 1}</Text>}

              <Text style={styles.cardText}>Temp: {item.temperature}</Text>
              {mode === "TS" && !compare && <Text style={styles.cardText}>Salinity: {item.salinity}</Text>}

              {mode === "TD" && !compare && (
                <>
                  <Text style={styles.cardText}>Depth: {item.depth}</Text>
                  <Text style={styles.cardText}>Pressure: {item.pressure}</Text>
                </>
              )}

              {compare && (
                <>
                  {typeof item.mean === "number" && (
                    <Text style={styles.cardText}>Mean: {item.mean.toFixed(3)}</Text>
                  )}
                  {typeof item.min === "number" && (
                    <Text style={styles.cardText}>Min: {item.min.toFixed(3)}</Text>
                  )}
                  {typeof item.max === "number" && (
                    <Text style={styles.cardText}>Max: {item.max.toFixed(3)}</Text>
                  )}
                  {typeof item.count === "number" && (
                    <Text style={styles.cardText}>Count: {item.count}</Text>
                  )}
                </>
              )}
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
    color: "#ffffff",
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 13,
    color: "#ffffff",
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
    color: "#ffffff",
    fontWeight: "600",
  },
  loading: {
    marginBottom: 8,
  },
  error: {
    color: "#fc8181",
    marginBottom: 8,
  },
  empty: {
    color: "#ffffff",
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
    color: "#ffffff",
    fontWeight: "600",
    marginBottom: 4,
  },
  cardText: {
    color: "#ffffff",
    fontSize: 13,
  },
  modeRow: {
    flexDirection: "row",
    marginBottom: 12,
  },
  modeButton: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "#4a5568",
    alignItems: "center",
    marginRight: 8,
  },
  modeButtonActive: {
    backgroundColor: "#38a169",
    borderColor: "#38a169",
  },
  modeButtonText: {
    color: "#ffffff",
    fontWeight: "600",
  },
  modeButtonTextActive: {
    color: "#ffffff",
  },
  compareRow: {
    marginBottom: 8,
  },
  compareButton: {
    paddingVertical: 8,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: "#4a5568",
    alignItems: "center",
  },
  graphContainer: {
    marginBottom: 12,
  },
  graphTitle: {
    color: "#ffffff",
    marginBottom: 4,
    fontSize: 13,
  },
  graphBarRow: {
    flexDirection: "row",
    alignItems: "flex-end",
    height: 40,
  },
  graphBar: {
    width: 4,
    marginHorizontal: 1,
    backgroundColor: "#ffffff",
  },
});
