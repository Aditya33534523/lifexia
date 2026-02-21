import os
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from backend.services.chat_store import append_message

upload_bp = Blueprint('upload', __name__, url_prefix='/api/upload')


@upload_bp.route('/image', methods=['POST'])
def upload_image():
    file = request.files.get('image')
    if file is None or file.filename == '':
        return jsonify({'error': 'No file uploaded'}), 400

    user_email = request.form.get('user_email', 'guest@lifexia.local')
    session_id = request.form.get('session_id') or None

    upload_folder = Path(current_app.config.get('UPLOAD_FOLDER', 'data/uploads'))
    upload_folder.mkdir(parents=True, exist_ok=True)

    filename = secure_filename(file.filename)
    file_path = upload_folder / filename
    file.save(file_path)

    extracted_text = f"Uploaded file: {filename}"
    ai_response = 'Thanks! Your file was uploaded successfully. OCR/analysis pipeline is not configured yet.'

    conversation = append_message(
        user_email,
        'user',
        f"Uploaded file: {filename}",
        session_id,
    )
    append_message(user_email, 'assistant', ai_response, conversation['session_id'])

    return jsonify(
        {
            'filename': filename,
            'file_path': os.fspath(file_path),
            'extracted_text': extracted_text,
            'ai_response': ai_response,
            'session_id': conversation['session_id'],
        }
    ), 200
