from flask import Flask, request, jsonify, render_template, send_file
import psycopg2
from image_processor import ImageProcessor
import uuid
import os
from datetime import datetime
import io

app = Flask(__name__)

# Configuração do banco de dados
db_config = {
    'dbname': 'imagedb',
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', 'postgres'),
    'host': os.environ.get('DB_HOST', 'postgres'),
    'port': '5432'
}

processor = None

@app.before_first_request
def setup():
    global processor
    processor = ImageProcessor(num_threads=4)
    processor.start_workers()
    
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS processed_images (
                id UUID PRIMARY KEY,
                original_data BYTEA,
                processed_data BYTEA,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                status VARCHAR(20)
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("Database setup completed!")
    except Exception as e:
        print(f"Setup error: {str(e)}")
        raise

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        
        # Get statistics
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing
            FROM processed_images
        """)
        stats_row = cur.fetchone()
        
        # Obter estatísticas das threads
        thread_stats = processor.get_stats() if processor else {
            'active_threads': 0,
            'total_threads': 4,
            'avg_process_time': 0,
            'queue_size': 0,
            'processed_count': 0
        }
        
        # Combinar estatísticas do banco e das threads
        stats = {
            'total_images': stats_row[0],
            'completed': stats_row[1],
            'processing': stats_row[2],
            'active_threads': thread_stats['active_threads'],
            'total_threads': thread_stats['total_threads'],
            'avg_process_time': round(thread_stats['avg_process_time'], 2),
            'queue_size': thread_stats['queue_size'],
            'processed_count': thread_stats['processed_count']
        }
        
        # Get recent images
        cur.execute("""
            SELECT id, status, uploaded_at, processed_at
            FROM processed_images
            ORDER BY uploaded_at DESC
            LIMIT 10
        """)
        recent_images = []
        for row in cur.fetchall():
            recent_images.append({
                'id': row[0],
                'status': row[1],
                'uploaded_at': row[2].strftime('%Y-%m-%d %H:%M:%S'),
                'processed_at': row[3].strftime('%Y-%m-%d %H:%M:%S') if row[3] else None
            })
            
        cur.close()
        conn.close()
        
        return render_template('dashboard.html', stats=stats, recent_images=recent_images)
    except Exception as e:
        print(f"Dashboard error: {str(e)}")  # Log do erro para debug
        return jsonify({'error': str(e)}), 500

@app.route('/upload', methods=['POST'])
def upload_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file'}), 400
            
        image_file = request.files['image']
        image_data = image_file.read()
        
        image_id = uuid.uuid4()
        
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO processed_images (id, original_data, status)
            VALUES (%s, %s, 'processing')
        """, (str(image_id), image_data))
        conn.commit()
        cur.close()
        conn.close()
        
        processor.add_image(str(image_id), image_data)
        
        return jsonify({
            'message': 'Image uploaded successfully',
            'image_id': str(image_id)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/status/<image_id>')
def status_page(image_id):
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        cur.execute("""
            SELECT status, processed_at
            FROM processed_images
            WHERE id = %s
        """, (image_id,))
        
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result is None:
            return "Image not found", 404
            
        return render_template('status.html', 
                             image_id=image_id,
                             status=result[0],
                             processed_at=result[1].strftime('%Y-%m-%d %H:%M:%S') if result[1] else None)
    except Exception as e:
        return str(e), 500

@app.route('/status/<image_id>/json')
def get_status(image_id):
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        cur.execute("""
            SELECT status, processed_at
            FROM processed_images
            WHERE id = %s
        """, (image_id,))
        
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result is None:
            return jsonify({'error': 'Image not found'}), 404
            
        return jsonify({
            'status': result[0],
            'processed_at': result[1].isoformat() if result[1] else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download/<image_id>')
def download_image(image_id):
    try:
        conn = psycopg2.connect(**db_config)
        cur = conn.cursor()
        cur.execute("""
            SELECT processed_data
            FROM processed_images
            WHERE id = %s AND status = 'completed'
        """, (image_id,))
        
        result = cur.fetchone()
        cur.close()
        conn.close()
        
        if result is None:
            return "Image not found or not processed", 404
            
        return send_file(
            io.BytesIO(result[0]),
            mimetype='image/jpeg',
            as_attachment=True,
            download_name=f'processed_{image_id}.jpg'
        )
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)