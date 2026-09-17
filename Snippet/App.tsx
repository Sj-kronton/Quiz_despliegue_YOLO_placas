import React, { useRef, useState } from 'react';
import {
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
  Image,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { CameraView, CameraType, useCameraPermissions } from 'expo-camera';
import axios from 'axios';

// ⚠️ Cambia esto por la IP pública (o dominio) de tu servidor en EC2
const BACKEND_URL = 'http://52.7.98.230:8080/predict/';

interface Caracter {
  caracter: string;
  confianza: number;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

interface Placa {
  texto: string;
  confianza_deteccion: number;
  bbox: { x1: number; y1: number; x2: number; y2: number };
  caracteres: Caracter[];
  recorte_base64: string | null;
}

interface PredictResponse {
  success: boolean;
  num_placas: number;
  placas: Placa[];
  image: string | null;
  message: string;
}

export default function App() {
  const cameraRef = useRef<CameraView>(null);
  const [permission, requestPermission] = useCameraPermissions();
  const [facing] = useState<CameraType>('back');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PredictResponse | null>(null);
  const [showCamera, setShowCamera] = useState(true);

  // --- Manejo de permisos de cámara ---
  if (!permission) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" />
      </View>
    );
  }

  if (!permission.granted) {
    return (
      <View style={styles.center}>
        <Text style={styles.info}>Necesitamos permiso para usar la cámara</Text>
        <TouchableOpacity style={styles.button} onPress={requestPermission}>
          <Text style={styles.buttonText}>Conceder permiso</Text>
        </TouchableOpacity>
      </View>
    );
  }

  // --- Tomar foto y enviarla al backend ---
  const tomarFotoYEnviar = async () => {
    if (!cameraRef.current) return;

    try {
      const photo = await cameraRef.current.takePictureAsync({ quality: 0.7 });
      if (!photo?.uri) return;

      setLoading(true);
      setShowCamera(false);

      const formData = new FormData();
      // FormData arma el multipart y el boundary automáticamente:
      // no hay que tocar headers de Content-Type a mano (a diferencia del curl manual).
      formData.append('file', {
        uri: photo.uri,
        name: 'foto.jpg',
        type: 'image/jpeg',
      } as any);

      const response = await axios.post<PredictResponse>(BACKEND_URL, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 30000,
      });

      setResult(response.data);
    } catch (error) {
      console.error(error);
      Alert.alert(
        'Error de conexión',
        'No se pudo procesar la imagen. Verifica que el servidor esté corriendo y accesible.'
      );
      setShowCamera(true);
    } finally {
      setLoading(false);
    }
  };

  const reiniciar = () => {
    setResult(null);
    setShowCamera(true);
  };

  // --- Vista de cámara ---
  if (showCamera) {
    return (
      <View style={styles.container}>
        <CameraView ref={cameraRef} style={styles.camera} facing={facing} />
        <View style={styles.controls}>
          <TouchableOpacity
            style={styles.captureButton}
            onPress={tomarFotoYEnviar}
            disabled={loading}
          >
            <Text style={styles.buttonText}>
              {loading ? 'Procesando...' : 'Tomar foto'}
            </Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  // --- Vista de resultados ---
  return (
    <ScrollView contentContainerStyle={styles.resultContainer}>
      {loading && <ActivityIndicator size="large" style={{ marginTop: 40 }} />}

      {!loading && result && (
        <>
          <Text style={styles.title}>
            {result.num_placas > 0
              ? `${result.num_placas} placa(s) detectada(s)`
              : 'No se detectó ninguna placa'}
          </Text>

          {/* Imagen completa anotada, devuelta por el servidor */}
          {result.image && (
            <Image
              source={{ uri: `data:image/jpeg;base64,${result.image}` }}
              style={styles.resultImage}
              resizeMode="contain"
            />
          )}

          {/* Una tarjeta por cada placa detectada */}
          {result.placas.map((placa, idx) => (
            <View key={idx} style={styles.placaCard}>
              <Text style={styles.placaTexto}>
                {placa.texto ? placa.texto : '(no se pudo leer el texto)'}
              </Text>
              <Text style={styles.placaDetalle}>
                Confianza de detección: {(placa.confianza_deteccion * 100).toFixed(1)}%
              </Text>
              <Text style={styles.placaDetalle}>
                Caracteres leídos: {placa.caracteres.length}
              </Text>
            </View>
          ))}

          <TouchableOpacity style={styles.button} onPress={reiniciar}>
            <Text style={styles.buttonText}>Tomar otra foto</Text>
          </TouchableOpacity>
        </>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  camera: { flex: 1 },
  controls: {
    position: 'absolute',
    bottom: 40,
    width: '100%',
    alignItems: 'center',
  },
  captureButton: {
    backgroundColor: '#2E7D32',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 50,
  },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 },
  info: { fontSize: 16, textAlign: 'center', marginBottom: 16 },
  button: {
    backgroundColor: '#1565C0',
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 8,
    marginTop: 16,
    alignSelf: 'center',
  },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  resultContainer: { padding: 20, paddingTop: 60, backgroundColor: '#fff', flexGrow: 1 },
  title: { fontSize: 20, fontWeight: '700', marginBottom: 16, textAlign: 'center' },
  resultImage: {
    width: '100%',
    height: 300,
    marginBottom: 20,
    backgroundColor: '#eee',
    borderRadius: 8,
  },
  placaCard: {
    backgroundColor: '#F1F8E9',
    borderRadius: 8,
    padding: 16,
    marginBottom: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#558B2F',
  },
  placaTexto: { fontSize: 24, fontWeight: '800', letterSpacing: 2 },
  placaDetalle: { fontSize: 13, color: '#555', marginTop: 4 },
});
