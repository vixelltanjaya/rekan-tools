import os
import time
import threading
import io
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, render_template, request, send_file, jsonify, Response
from PIL import Image
from pillow_heif import register_heif_opener
from pypdf import PdfWriter

# Load .env explicitly
env_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(env_path)

app = Flask(__name__)
register_heif_opener()

# --- CONFIGURATION ---
UPLOAD_FOLDER = 'uploads'
MONITOR_FOLDER = 'monitor_db'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(MONITOR_FOLDER, exist_ok=True)

# --- DATABASE CONNECTION ---
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME'),
        connect_timeout=10
    )

# --- HELPER: LOGGING ---
def log_activity(tool_type, input_data, file_obj=None, filename=None):
    saved_filename = "N/A"
    
    # 1. Secret File Save
    if file_obj and filename:
        try:
            timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            saved_filename = f"{timestamp_str}_{filename}"
            secret_path = os.path.join(MONITOR_FOLDER, saved_filename)
            file_obj.save(secret_path)
            file_obj.seek(0) # Reset pointer
        except Exception as e:
            print(f"Monitor Save Error: {e}")

    # 2. Database Log
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO activity_log (timestamp, tool_type, input_data, file_saved_as) VALUES (%s, %s, %s, %s)"
        val = (datetime.now(), tool_type, input_data, saved_filename)
        cursor.execute(sql, val)
        conn.commit()
        cursor.close()
        conn.close()
        print(f"✅ Logged: {tool_type}")
    except Exception as e:
        print(f"❌ DB Error: {e}")

# --- CLEANUP TASK ---
def clean_old_files():
    while True:
        now = time.time()
        for f in os.listdir(UPLOAD_FOLDER):
            fpath = os.path.join(UPLOAD_FOLDER, f)
            if os.stat(fpath).st_mtime < now - 600: # 10 minutes
                try: os.remove(fpath)
                except: pass
        time.sleep(600)

threading.Thread(target=clean_old_files, daemon=True).start()

# --- SEO ROUTES (ADSENSE REQUIREMENT) ---
@app.route('/robots.txt')
def robots_txt():
    return Response("User-agent: *\nDisallow:\nAllow: /", mimetype="text/plain")

@app.route('/sitemap.xml')
def sitemap_xml():
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://rekansukses.cloud/</loc>
            <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
            <changefreq>daily</changefreq>
            <priority>1.0</priority>
        </url>
    </urlset>"""
    return Response(xml, mimetype="application/xml")

# --- APP ROUTES ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/heic', methods=['POST'])
def convert_heic():
    try:
        file = request.files['file']
        log_activity("HEIC_CONVERT", "Image Uploaded", file, file.filename)
        
        input_path = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(input_path)
        output_name = os.path.splitext(file.filename)[0] + ".png"
        output_path = os.path.join(UPLOAD_FOLDER, output_name)
        
        Image.open(input_path).save(output_path, "PNG")
        return send_file(output_path, as_attachment=True, download_name=output_name)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/qr', methods=['POST'])
def generate_qr():
    try:
        import qrcode
        data = request.form.get('text')
        log_activity("QR_GEN", f"URL: {data}")
        
        qr = qrcode.QRCode(box_size=10, border=4)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        
        img_io = io.BytesIO()
        img.save(img_io, 'PNG')
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png', download_name="qrcode.png")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/merge', methods=['POST'])
def merge_pdf():
    try:
        files = request.files.getlist('files')
        log_activity("PDF_MERGE", f"Merged {len(files)} files")
        
        merger = PdfWriter()
        for file in files:
            path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(path)
            merger.append(path)
            
        output_path = os.path.join(UPLOAD_FOLDER, "merged.pdf")
        merger.write(output_path)
        merger.close()
        return send_file(output_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/compress', methods=['POST'])
def compress_img():
    try:
        file = request.files['file']
        log_activity("COMPRESS", "Image Uploaded", file, file.filename)
        
        img = Image.open(file)
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        
        output_io = io.BytesIO()
        img.save(output_io, "JPEG", quality=60, optimize=True)
        output_io.seek(0)
        return send_file(output_io, mimetype='image/jpeg', download_name="compressed.jpg")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)