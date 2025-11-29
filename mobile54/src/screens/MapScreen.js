import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  TextInput,
  ScrollView,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context"; // ← new one
import MapView, { Polyline, Marker } from "react-native-maps";
import { fetchTrajectoriesInRadius } from "../config/api";

export default function MapScreen() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [trajectories, setTrajectories] = useState([]);
  const [selectedFloatId, setSelectedFloatId] = useState("");

  // Map center and radius controls
  const [centerLat, setCenterLat] = useState("-2");
  const [centerLon, setCenterLon] = useState("80");
  const [radius, setRadius] = useState("2000");

  // Load trajectories on mount
  useEffect(() => {
    loadTrajectories();
  }, []);

  const loadTrajectories = async () => {
    setLoading(true);
    setError(null);
    try {
      const lat = parseFloat(centerLat) || -2;
      const lon = parseFloat(centerLon) || 80;
      const rad = parseFloat(radius) || 2000;

      const data = await fetchTrajectoriesInRadius(lat, lon, rad, 100);
      setTrajectories(data?.trajectories || []);
    } catch (e) {
      setError(e.message || String(e));
      setTrajectories([]);
    } finally {
      setLoading(false);
    }
  };

  // Group trajectories by float_id
  const floatGroups = trajectories.reduce((acc, point) => {
    const fid = String(point.floatId);
    if (!acc[fid]) acc[fid] = [];
    acc[fid].push(point);
    return acc;
  }, {});

  // Sort each float's points by cycle number
  Object.keys(floatGroups).forEach((fid) => {
    floatGroups[fid].sort(
      (a, b) => (a.cycleNumber || 0) - (b.cycleNumber || 0)
    );
  });

  const floatIds = Object.keys(floatGroups);
  const visibleFloatIds = selectedFloatId ? [selectedFloatId] : floatIds;

  // Colors for different floats
  const colors = [
    "#e41a1c",
    "#377eb8",
    "#4daf4a",
    "#984ea3",
    "#ff7f00",
    "#a65628",
  ];

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.inner}>
        <Text style={styles.title}>Float Trajectories</Text>
        <Text style={styles.subtitle}>Indian Ocean float paths over time</Text>

        {/* Controls */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.controlRow}
        >
          <View style={styles.controls}>
            <Text style={styles.label}>Lat:</Text>
            <TextInput
              style={styles.input}
              value={centerLat}
              onChangeText={setCenterLat}
              keyboardType="numeric"
              placeholder="-2"
            />

            <Text style={styles.label}>Lon:</Text>
            <TextInput
              style={styles.input}
              value={centerLon}
              onChangeText={setCenterLon}
              keyboardType="numeric"
              placeholder="80"
            />

            <Text style={styles.label}>Radius (km):</Text>
            <TextInput
              style={styles.input}
              value={radius}
              onChangeText={setRadius}
              keyboardType="numeric"
              placeholder="2000"
            />

            {/* Fixed button – everything is now inside the TouchableOpacity */}
            <TouchableOpacity
              style={styles.smallButton}
              onPress={loadTrajectories}
              disabled={loading}
            >
              <Text style={styles.smallButtonText}>
                {loading ? "..." : "Reload"}
              </Text>
            </TouchableOpacity>
          </View>
        </ScrollView>

        {/* Float selector */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={styles.floatRow}
          contentContainerStyle={{ alignItems: "center" }}
        >
          <TouchableOpacity
            style={[
              styles.floatChip,
              !selectedFloatId && styles.floatChipActive,
            ]}
            onPress={() => setSelectedFloatId("")}
          >
            <Text style={styles.floatChipText}>All ({floatIds.length})</Text>
          </TouchableOpacity>

          {floatIds.slice(0, 10).map((fid) => (
            <TouchableOpacity
              key={fid}
              style={[
                styles.floatChip,
                selectedFloatId === fid && styles.floatChipActive,
              ]}
              onPress={() => setSelectedFloatId(fid)}
            >
              <Text style={styles.floatChipText}>{fid}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {loading && <ActivityIndicator style={styles.loading} />}
        {error && <Text style={styles.error}>Error: {error}</Text>}

        {/* Map */}
        <MapView
          style={styles.map}
          initialRegion={{
            latitude: parseFloat(centerLat) || -2,
            longitude: parseFloat(centerLon) || 80,
            latitudeDelta: 50,
            longitudeDelta: 50,
          }}
        >
          {visibleFloatIds.map((fid, idx) => {
            const points = floatGroups[fid] || [];
            if (points.length === 0) return null;

            const color = colors[idx % colors.length];
            const coordinates = points.map((p) => ({
              latitude: p.lat,
              longitude: p.lon,
            }));

            const lastPoint = points[points.length - 1];

            return (
              <React.Fragment key={fid}>
                {/* Trajectory line */}
                <Polyline
                  coordinates={coordinates}
                  strokeColor={color}
                  strokeWidth={2}
                  lineDashPattern={[4, 8]}
                />

                {/* Current position marker */}
                <Marker
                  coordinate={{
                    latitude: lastPoint.lat,
                    longitude: lastPoint.lon,
                  }}
                  pinColor={color}
                  title={`Float ${fid}`}
                  description={`Cycle: ${lastPoint.cycleNumber || "N/A"}`}
                />
              </React.Fragment>
            );
          })}
        </MapView>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0b1020" },
  inner: { flex: 1, padding: 16 },
  title: { fontSize: 24, fontWeight: "700", color: "#fff", marginBottom: 4 },
  subtitle: { fontSize: 13, color: "#a0aec0", marginBottom: 12 },
  controlRow: { maxHeight: 50, marginBottom: 8 },
  controls: { flexDirection: "row", alignItems: "center", gap: 8 },
  label: { color: "#a0aec0", fontSize: 12 },
  input: {
    borderRadius: 8,
    borderWidth: 1,
    borderColor: "#2d3748",
    paddingHorizontal: 8,
    paddingVertical: 4,
    color: "#edf2f7",
    fontSize: 12,
    width: 60,
  },
  smallButton: {
    backgroundColor: "#805ad5",
    borderRadius: 999,
    paddingHorizontal: 12,
    paddingVertical: 6,
    justifyContent: "center",
    alignItems: "center",
  },
  smallButtonText: { color: "#fff", fontWeight: "600", fontSize: 12 },
  floatRow: { maxHeight: 44, marginBottom: 8 },
  floatChip: {
    backgroundColor: "#1a202c",
    borderRadius: 999,
    paddingHorizontal: 12,
    marginRight: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: "#2d3748",
    height: 36,
    justifyContent: "center",
  },
  floatChipActive: {
    backgroundColor: "#805ad5",
    borderColor: "#805ad5",
  },
  floatChipText: { color: "#fff", fontSize: 12 },
  loading: { marginBottom: 8 },
  error: { color: "#fc8181", marginBottom: 8, fontSize: 12 },
  map: { flex: 1, borderRadius: 12, overflow: "hidden" },
});
