import threading
import queue
import time
from PIL import Image
import io
import psycopg2
from datetime import datetime
import os

class ImageProcessor:
    def __init__(self, num_threads=4):
        self.processing_queue = queue.Queue()
        self.num_threads = num_threads
        self.threads = []
        self.active_threads = 0
        self.processed_count = 0
        self.processing_times = []
        
        self.db_config = {
            'dbname': 'imagedb',
            'user': os.environ.get('DB_USER', 'postgres'),
            'password': os.environ.get('DB_PASSWORD', 'postgres'),
            'host': os.environ.get('DB_HOST', 'postgres'),
            'port': '5432'
        }
        print(f"Database config: {self.db_config}")
        
    def start_workers(self):
        """Inicia as threads trabalhadoras"""
        print("Starting worker threads...")
        for _ in range(self.num_threads):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self.threads.append(t)
            
    def _worker(self):
        """Função executada por cada thread worker"""
        while True:
            try:
                self.active_threads += 1
                image_data = self.processing_queue.get(timeout=5)
                if image_data is None:
                    break
                
                start_time = time.time()
                image_id, image_bytes = image_data
                
                print(f"Processing image {image_id}")
                processed_data = self._process_image(image_bytes)
                self._save_to_db(image_id, processed_data)
                
                process_time = time.time() - start_time
                self.processing_times.append(process_time)
                self.processed_count += 1
                
                print(f"Finished processing image {image_id} in {process_time:.2f} seconds")
                self.processing_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in worker: {e}")
            finally:
                self.active_threads -= 1
                
    def _process_image(self, image_bytes):
        """Processa uma imagem individual"""
        try:
            # Carrega a imagem
            image = Image.open(io.BytesIO(image_bytes))
            
            # Exemplo de processamento: redimensiona para thumbnail
            max_size = (800, 800)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Converte de volta para bytes
            output = io.BytesIO()
            image.save(output, format='JPEG')
            processed_bytes = output.getvalue()
            
            return processed_bytes
            
        except Exception as e:
            print(f"Erro no processamento: {e}")
            return None
            
    def _save_to_db(self, image_id, processed_data):
        """Salva os resultados no PostgreSQL"""
        try:
            print(f"Saving to database: {image_id}")
            conn = psycopg2.connect(**self.db_config)
            cur = conn.cursor()
            
            cur.execute("""
                UPDATE processed_images 
                SET processed_data = %s,
                    processed_at = %s,
                    status = 'completed'
                WHERE id = %s
            """, (processed_data, datetime.now(), image_id))
            
            conn.commit()
            cur.close()
            conn.close()
            print(f"Successfully saved image {image_id}")
            
        except Exception as e:
            print(f"Erro ao salvar no banco: {e}")
            
    def add_image(self, image_id, image_bytes):
        """Adiciona uma imagem à fila de processamento"""
        print(f"Adding image {image_id} to processing queue")
        self.processing_queue.put((image_id, image_bytes))
        
    def get_stats(self):
        """Retorna estatísticas do processador"""
        return {
            'active_threads': self.active_threads,
            'total_threads': self.num_threads,
            'processed_count': self.processed_count,
            'avg_process_time': sum(self.processing_times) / len(self.processing_times) if self.processing_times else 0,
            'queue_size': self.processing_queue.qsize()
        }
        
    def shutdown(self):
        """Finaliza todas as threads trabalhadoras"""
        for _ in self.threads:
            self.processing_queue.put(None)
        for t in self.threads:
            t.join()