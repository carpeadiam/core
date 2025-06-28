from flask import Flask, send_file, jsonify
from flask_cors import CORS
from mini import CrosswordGenerator
from connections import create_connections_game
from datetime import datetime


app = Flask(__name__)
CORS(app)

@app.route('/mini')
def download_puz():
    
    generator = CrosswordGenerator(size=8)
    # Load word clues
    word_clues = generator.load_from_json_file("short_word_clues.json")
    
    if generator.generate_crossword(word_clues, target_words=8):
        # Print the crossword
        generator.print_grid()
        generator.print_clues()
        generator.print_solution()
        
        # Export to JSON
        generator.export_to_json("generated_crossword.json")
        
        # Export to .puz format
        generator.export_to_puz(
            "generated_crossword.puz",
            title="Core Games Mini",
            author="thecodeworks",
            copyright=f"© {datetime.now().year}"
        )
    else:
        print("Failed to generate crossword with enough connected words")

    return send_file('generated_crossword.puz', as_attachment=True, download_name='generated_crossword.puz', mimetype='application/octet-stream')

@app.route('/connections')
def connections_game():
    return jsonify(create_connections_game())

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
