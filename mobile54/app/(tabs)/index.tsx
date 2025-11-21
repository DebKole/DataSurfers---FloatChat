import React, { useEffect, useState } from 'react';
import { SafeAreaView, View, Text, StyleSheet, Button, ActivityIndicator } from 'react-native';

import { pingBackend } from '@/src/config/api';

export default function HomeScreen() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handlePing = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await pingBackend();
      setMessage(JSON.stringify(data));
    } catch (e: any) {
      setError(e?.message || String(e));
      setMessage(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    handlePing();
  }, []);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.title}>FloatChat Mobile</Text>
        <Text style={styles.subtitle}>Connected to your FastAPI backend</Text>

        <Button title="Refresh" onPress={handlePing} />

        {loading && <ActivityIndicator style={styles.status} />}
        {error && <Text style={[styles.status, styles.error]}>Error: {error}</Text>}
        {message && <Text style={styles.status}>{message}</Text>}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0b1020' },
  content: {
    flex: 1,
    padding: 24,
    justifyContent: 'center',
    alignItems: 'center',
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 14,
    color: '#a0aec0',
    marginBottom: 24,
    textAlign: 'center',
  },
  status: {
    marginTop: 16,
    color: '#e2e8f0',
    textAlign: 'center',
  },
  error: {
    color: '#f56565',
  },
});
