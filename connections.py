import json
import random

def create_connections_game(input_json='cwords.json', output_json='cgame.json'):
    """
    Creates a NYT Connections game with:
    - 1 random category per difficulty (Easiest, Easy, Medium, Hard)
    - 4 random words per category
    - All 16 words shuffled together in 'all_words'
    
    Output structure:
    {
        "categories": {
            "Easiest": {"category_name": ["word1", "word2", "word3", "word4"]},
            "Easy": {"category_name": [...]},
            "Medium": {...},
            "Hard": {...}
        },
        "all_words": ["shuffled", "list", "of", "16", "words"]
    }
    """
    # Load the word data
    with open(input_json, 'r') as f:
        word_data = json.load(f)
    
    # Prepare the game data
    game_data = {
        "categories": {},
        "all_words": []
    }
    
    # Process each difficulty level
    for difficulty in ["Easiest", "Easy", "Medium", "Hard"]:
        if difficulty not in word_data:
            print(f"Warning: Difficulty '{difficulty}' not found in data.")
            continue
        
        # Get all categories with at least 4 words
        valid_categories = {
            cat: words for cat, words in word_data[difficulty].items()
            if len(words) >= 4
        }
        
        if not valid_categories:
            print(f"Warning: No valid categories for {difficulty} (needs ≥4 words).")
            continue
        
        # Randomly pick 1 category and 4 words from it
        chosen_category = random.choice(list(valid_categories.keys()))
        chosen_words = random.sample(valid_categories[chosen_category], 4)
        
        game_data["categories"][difficulty] = {chosen_category: chosen_words}
        game_data["all_words"].extend(chosen_words)
    
    # Shuffle all words for the game board
    random.shuffle(game_data["all_words"])
    
    # Save the game
    with open(output_json, 'w') as f:
        json.dump(game_data, f, indent=2)
    
    print(f"Connections game saved to {output_json}")
    return game_data

