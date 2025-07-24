import unittest
import time
import json
import threading
import queue
from unittest.mock import MagicMock, patch

# Simulation des classes et fonctions nécessaires
class MockResponse:
    def __init__(self, content, status_code=200):
        self.content = content
        self.status_code = status_code

    def iter_content(self, chunk_size=1024):
        chunks = [self.content[i:i+chunk_size] for i in range(0, len(self.content), chunk_size)]
        for chunk in chunks:
            yield chunk

class MockSettings:
    AI_MODEL = "gpt-4"
    AI_TEMPERATURE = 0.7
    AI_MAX_TOKENS = 2000
    STREAMING_ENABLED = True
    STREAMING_CHUNK_SIZE = 10

class TestStreaming(unittest.TestCase):
    """Tests pour la fonctionnalité de streaming des réponses de l'assistant IA"""
    
    def setUp(self):
        """Configuration initiale pour les tests"""
        self.settings = MockSettings()
        self.mock_queue = queue.Queue()
    
    def test_streaming_response(self):
        """Test du streaming de réponses"""
        # Fonction simulant le streaming de réponses
        def stream_response(prompt, callback, settings):
            response_text = f"Voici une réponse de test pour: {prompt}"
            chunks = [response_text[i:i+settings.STREAMING_CHUNK_SIZE] 
                     for i in range(0, len(response_text), settings.STREAMING_CHUNK_SIZE)]
            
            for chunk in chunks:
                callback(chunk)
                time.sleep(0.01)  # Petite pause pour simuler le streaming
            
            return response_text
        
        # Fonction de callback qui stocke les chunks dans une queue
        def collect_chunks(chunk):
            self.mock_queue.put(chunk)
        
        # Exécution du streaming
        prompt = "Test de streaming"
        full_response = stream_response(prompt, collect_chunks, self.settings)
        
        # Récupération des chunks de la queue
        collected_chunks = []
        while not self.mock_queue.empty():
            collected_chunks.append(self.mock_queue.get())
        
        # Vérifications
        self.assertEqual("".join(collected_chunks), full_response)
        self.assertTrue(len(collected_chunks) > 1)  # Plusieurs chunks ont été envoyés
    
    @patch('requests.post')
    def test_streaming_api_call(self, mock_post):
        """Test d'un appel d'API avec streaming"""
        # Configuration du mock pour simuler une réponse en streaming
        mock_response = MockResponse(b'{"id":"resp1","choices":[{"delta":{"content":"Chunk1"}}]}\n' +
                                    b'{"id":"resp2","choices":[{"delta":{"content":"Chunk2"}}]}\n' +
                                    b'{"id":"resp3","choices":[{"delta":{"content":"Chunk3"}}]}')
        mock_post.return_value = mock_response
        
        # Fonction simulant un appel d'API avec streaming
        def call_streaming_api(prompt, settings):
            headers = {"Content-Type": "application/json"}
            data = {
                "model": settings.AI_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": settings.AI_TEMPERATURE,
                "max_tokens": settings.AI_MAX_TOKENS,
                "stream": True
            }
            
            response = mock_post("https://api.example.com/v1/chat/completions", 
                               headers=headers, 
                               json=data, 
                               stream=True)
            
            full_text = ""
            for chunk in response.iter_content():
                if chunk:
                    # Traitement des données en streaming
                    try:
                        lines = chunk.decode('utf-8').strip().split('\n')
                        for line in lines:
                            if line and line != "data: [DONE]":
                                json_data = json.loads(line.replace("data: ", ""))
                                if "choices" in json_data and json_data["choices"]:
                                    content = json_data["choices"][0].get("delta", {}).get("content", "")
                                    full_text += content
                    except Exception as e:
                        print(f"Erreur lors du traitement du chunk: {e}")
            
            return full_text
        
        # Exécution de l'appel d'API
        result = call_streaming_api("Test prompt", self.settings)
        
        # Vérifications
        self.assertEqual(result, "Chunk1Chunk2Chunk3")
        mock_post.assert_called_once()
    
    def test_threaded_streaming(self):
        """Test du streaming dans un thread séparé"""
        result_queue = queue.Queue()
        
        # Fonction simulant le traitement de streaming dans un thread
        def streaming_worker(prompt, result_queue):
            chunks = ["Partie 1: ", "Ceci est ", "une réponse ", "en streaming"]
            full_response = ""
            
            for chunk in chunks:
                full_response += chunk
                result_queue.put(("chunk", chunk))
                time.sleep(0.05)
            
            result_queue.put(("complete", full_response))
        
        # Démarrage du thread de streaming
        prompt = "Test thread"
        thread = threading.Thread(target=streaming_worker, args=(prompt, result_queue))
        thread.start()
        
        # Collecte des résultats
        chunks = []
        final_result = None
        
        # Attente des résultats avec timeout
        timeout = time.time() + 1.0
        while time.time() < timeout and (not final_result or not thread.is_alive()):
            try:
                item_type, content = result_queue.get(timeout=0.1)
                if item_type == "chunk":
                    chunks.append(content)
                elif item_type == "complete":
                    final_result = content
            except queue.Empty:
                pass
        
        # Attente de la fin du thread
        thread.join(timeout=0.5)
        
        # Vérifications
        self.assertFalse(thread.is_alive())
        self.assertEqual(len(chunks), 4)
        self.assertEqual("".join(chunks), "Partie 1: Ceci est une réponse en streaming")
        if final_result:
            self.assertEqual(final_result, "".join(chunks))

if __name__ == '__main__':
    unittest.main() 