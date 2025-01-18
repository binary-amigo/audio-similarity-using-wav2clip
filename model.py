from flask import Flask, request, jsonify
import wav2clip
import librosa
import numpy as np
import os
from sklearn.metrics.pairwise import cosine_similarity

# Folder containing the audio database
AUDIO_DATABASE_DIR = 'audio_database'

# Threshold for similarity (tweak as needed)
SIMILARITY_THRESHOLD = 0.85

# Function to compute cosine similarity
def calculate_similarity(embedding1, embedding2):
    embedding1 = np.array(embedding1).reshape(1, -1)
    embedding2 = np.array(embedding2).reshape(1, -1)
    similarity = cosine_similarity(embedding1, embedding2)[0][0]
    return similarity

# Function to get audio embeddings
def get_audio_embedding(audio_path):
    model = wav2clip.get_model()
    waveform, sample_rate = librosa.load(audio_path, sr=None)
    embeddings = wav2clip.embed_audio(waveform, model)
    return embeddings

# Initialize Flask app
app = Flask(__name__)

# API endpoint to receive audio and find the best match in the database
@app.route('/find_match', methods=['POST'])
def find_match():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Save the uploaded file temporarily
    uploaded_file_path = 'temp_uploaded_audio.wav'
    file.save(uploaded_file_path)

    try:
        # Get the embedding for the uploaded audio
        emb_uploaded = get_audio_embedding(uploaded_file_path)

        # List all files in the audio database
        audio_files = os.listdir(AUDIO_DATABASE_DIR)
        best_match_score = -1
        best_match_file = None

        for audio_file in audio_files:
            audio_path = os.path.join(AUDIO_DATABASE_DIR, audio_file)

            # Get the embedding for the database audio
            emb_db = get_audio_embedding(audio_path)

            # Calculate cosine similarity
            similarity = calculate_similarity(emb_uploaded, emb_db)

            # Check if similarity exceeds threshold and is the best match so far
            if similarity > best_match_score:
                best_match_score = similarity
                best_match_file = audio_file

        # Clean up the temporary uploaded file
        if os.path.exists(uploaded_file_path):
            os.remove(uploaded_file_path)

        # Convert float32 to standard float
        best_match_score = float(best_match_score)

        # Return the result
        if best_match_score >= SIMILARITY_THRESHOLD:
            return jsonify({
                'match_found': True,
                'match_id': best_match_file,
                'similarity': best_match_score
            })
        else:
            return jsonify({'match_found': False})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
