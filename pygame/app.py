from flask import Flask, render_template, jsonify, request
from engine import GameEngine

app = Flask(__name__)

# Inisialisasi Game Engine (Pygame berjalan di background)
game = GameEngine()

@app.route("/")
def index():
    # Reset game setiap kali halaman dimuat ulang (opsional)
    game.reset()
    return render_template("index.html")

@app.route("/api/move", methods=["POST"])
def move():
    # Terima input dari JS
    data = request.json
    direction = data.get("direction", "")
    
    # Kirim ke Pygame Engine untuk diproses
    state = game.process_input(direction)
    
    return jsonify(state)

@app.route("/api/answer", methods=["POST"])
def answer():
    data = request.json
    answer_idx = data.get("answer_idx")
    
    # Cek jawaban (Logic sederhana, bisa dipindah ke engine jika mau lebih strict)
    # Ambil soal saat ini
    from data import questions
    current_q = questions[game.current_q_index % len(questions)]
    is_correct = (answer_idx == current_q["answer"])
    
    # Update state di engine
    new_state = game.answer_quiz(is_correct)
    
    return jsonify({
        "correct": is_correct,
        "score": new_state["score"],
        "level": new_state["level"],
        "player_x": new_state["player_x"]
    })

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)