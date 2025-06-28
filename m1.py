import json
import random
import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from copy import deepcopy

@dataclass
class Word:
    text: str
    clue: str
    row: int
    col: int
    direction: str  # 'across' or 'down'
    number: int

class CrosswordGenerator:
    def __init__(self, size: int = 10):
        self.size = size
        self.grid = [[' ' for _ in range(size)] for _ in range(size)]
        self.placed_words = []
        self.word_numbers = {}
        
    def validate_word(self, word: str) -> bool:
        """Check if word contains only letters (no numbers, spaces, or special characters)"""
        return bool(re.match(r'^[A-Za-z]+$', word))
    
    def load_from_json_file(self, filename: str = "short_word_clues.json") -> Dict[str, List[str]]:
        """Load word-clue pairs from JSON file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Filter out invalid words
            valid_data = {}
            for word, clues in data.items():
                if self.validate_word(word):
                    valid_data[word.upper()] = clues
                else:
                    print(f"Warning: Skipping invalid word '{word}' (contains numbers, spaces, or special characters)")
            print(f"Loaded {len(valid_data)} valid words from {filename}")
            return valid_data
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found!")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON from {filename}: {e}")
            return {}
        except Exception as e:
            print(f"Error reading file {filename}: {e}")
            return {}
    
    def can_place_word(self, word: str, row: int, col: int, direction: str) -> bool:
        """Check if a word can be placed at the given position"""
        if direction == 'across':
            if col + len(word) > self.size:
                return False
            
            # Check space before word (must be empty or edge)
            if col > 0 and self.grid[row][col-1] != ' ':
                return False
            
            # Check space after word (must be empty or edge)
            if col + len(word) < self.size and self.grid[row][col + len(word)] != ' ':
                return False
            
            # Check each letter position
            for i, letter in enumerate(word):
                curr_row, curr_col = row, col + i
                if self.grid[curr_row][curr_col] != ' ' and self.grid[curr_row][curr_col] != letter:
                    return False
                # Check perpendicular conflicts only for empty cells
                if self.grid[curr_row][curr_col] == ' ':
                    # Check above
                    if curr_row > 0 and self.grid[curr_row-1][curr_col] != ' ':
                        return False
                    # Check below
                    if curr_row < self.size-1 and self.grid[curr_row+1][curr_col] != ' ':
                        return False
        else:  # down
            if row + len(word) > self.size:
                return False
            
            # Check space before word (must be empty or edge)
            if row > 0 and self.grid[row-1][col] != ' ':
                return False
            
            # Check space after word (must be empty or edge)
            if row + len(word) < self.size and self.grid[row + len(word)][col] != ' ':
                return False
            
            # Check each letter position
            for i, letter in enumerate(word):
                curr_row, curr_col = row + i, col
                if self.grid[curr_row][curr_col] != ' ' and self.grid[curr_row][curr_col] != letter:
                    return False
                # Check perpendicular conflicts only for empty cells
                if self.grid[curr_row][curr_col] == ' ':
                    # Check left
                    if curr_col > 0 and self.grid[curr_row][curr_col-1] != ' ':
                        return False
                    # Check right
                    if curr_col < self.size-1 and self.grid[curr_row][curr_col+1] != ' ':
                        return False
        return True
    
    def place_word(self, word: str, row: int, col: int, direction: str, clue: str, number: int):
        """Place a word on the grid"""
        if direction == 'across':
            for i, letter in enumerate(word):
                self.grid[row][col + i] = letter
        else:  # down
            for i, letter in enumerate(word):
                self.grid[row + i][col] = letter
        
        word_obj = Word(word, clue, row, col, direction, number)
        self.placed_words.append(word_obj)
        self.word_numbers[(row, col)] = number
    
    def find_intersections(self, word: str, placed_word: Word) -> List[Tuple[int, int, int, int, str]]:
        """Find possible intersections between a word and a placed word"""
        intersections = []
        
        for i, letter1 in enumerate(word):
            for j, letter2 in enumerate(placed_word.text):
                if letter1 == letter2:
                    if placed_word.direction == 'across':
                        # New word goes down
                        new_row = placed_word.row - i
                        new_col = placed_word.col + j
                        if (new_row >= 0 and new_row + len(word) <= self.size and 
                            new_col >= 0 and new_col < self.size):
                            intersections.append((new_row, new_col, i, j, 'down'))
                    else:
                        # New word goes across
                        new_row = placed_word.row + j
                        new_col = placed_word.col - i
                        if (new_col >= 0 and new_col + len(word) <= self.size and 
                            new_row >= 0 and new_row < self.size):
                            intersections.append((new_row, new_col, i, j, 'across'))
        
        return intersections
    
    def generate_crossword(self, word_clues: Dict[str, List[str]], target_words: int = 8) -> bool:
        """Generate a crossword puzzle with NO floating/isolated words"""
        if not word_clues:
            print("No valid words provided")
            return False
        
        # Reset grid
        self.grid = [[' ' for _ in range(self.size)] for _ in range(self.size)]
        self.placed_words = []
        self.word_numbers = {}
        
        # Randomly select and shuffle words
        all_words = list(word_clues.items())
        random.shuffle(all_words)
        
        # Convert to list of (word, clue) pairs with random clue selection
        word_list = []
        for word, clues in all_words:
            if clues:
                word_list.append((word, random.choice(clues)))
        
        if not word_list:
            print("No words with clues found")
            return False
        
        # Start with a random word from the shuffled list
        first_word, first_clue = word_list[0]
        start_row = self.size // 2
        start_col = (self.size - len(first_word)) // 2
        
        # Ensure first word fits
        if start_col < 0:
            start_col = 0
        if start_col + len(first_word) > self.size:
            start_col = self.size - len(first_word)
            
        self.place_word(first_word, start_row, start_col, 'across', first_clue, 1)
        
        word_number = 2
        placed_count = 1
        max_attempts = 200
        
        # Try to place remaining words - ONLY if they intersect with existing words
        for word, clue in word_list[1:]:
            if placed_count >= target_words:
                break
                
            placed = False
            attempts = 0
            
            # ONLY try to intersect with existing words - NO isolated placement
            while attempts < max_attempts and not placed:
                # Randomly try different existing words for intersection
                existing_words = self.placed_words.copy()
                random.shuffle(existing_words)
                
                for placed_word in existing_words:
                    intersections = self.find_intersections(word, placed_word)
                    if intersections:
                        random.shuffle(intersections)
                        
                        for row, col, word_idx, placed_idx, direction in intersections:
                            if self.can_place_word(word, row, col, direction):
                                self.place_word(word, row, col, direction, clue, word_number)
                                word_number += 1
                                placed_count += 1
                                placed = True
                                break
                    
                    if placed:
                        break
                
                attempts += 1
            
            if not placed:
                print(f"Could not place word '{word}' with intersection - skipping to avoid floating words")
        
        print(f"Successfully placed {placed_count} connected words")
        return placed_count >= 7  # Ensure at least 7 words
    
    def print_grid(self):
        """Print the crossword grid nicely formatted"""
        print("\n" + "="*60)
        print("CROSSWORD PUZZLE")
        print("="*60)
        
        # Print column numbers
        print("   ", end="")
        for i in range(self.size):
            print(f"{i:2d}", end=" ")
        print()
        
        # Print grid with row numbers
        for i, row in enumerate(self.grid):
            print(f"{i:2d} ", end="")
            for cell in row:
                if cell == ' ':
                    print(" ■", end=" ")
                else:
                    print(f" {cell}", end=" ")
            print()
        
        print("\n" + "="*60)
    
    def print_clues(self):
        """Print the clues organized by direction"""
        if not self.placed_words:
            print("No words placed yet!")
            return
        
        across_words = [w for w in self.placed_words if w.direction == 'across']
        down_words = [w for w in self.placed_words if w.direction == 'down']
        
        across_words.sort(key=lambda x: x.number)
        down_words.sort(key=lambda x: x.number)
        
        print("\nACROSS:")
        print("-" * 40)
        for word in across_words:
            print(f"{word.number:2d}. {word.clue}")
        
        print("\nDOWN:")
        print("-" * 40)
        for word in down_words:
            print(f"{word.number:2d}. {word.clue}")
        print()
    
    def print_solution(self):
        """Print the solution with word positions"""
        print("\nSOLUTION:")
        print("="*60)
        for word in sorted(self.placed_words, key=lambda x: x.number):
            print(f"{word.number:2d}. {word.text} ({word.direction}) - Row {word.row}, Col {word.col}")
        print()
    
    def export_to_json(self, filename: str = "crossword_puzzle.json"):
        """Export the crossword puzzle to JSON format"""
        if not self.placed_words:
            print("No crossword to export!")
            return
        
        # Create grid representation
        grid_data = []
        for row in self.grid:
            grid_data.append([''.join(row)])
        
        # Create words data
        words_data = []
        for word in self.placed_words:
            words_data.append({
                "word": word.text,
                "clue": word.clue,
                "row": word.row,
                "col": word.col,
                "direction": word.direction,
                "number": word.number
            })
        
        # Create clues data
        across_clues = {}
        down_clues = {}
        
        for word in self.placed_words:
            if word.direction == 'across':
                across_clues[str(word.number)] = word.clue
            else:
                down_clues[str(word.number)] = word.clue
        
        crossword_data = {
            "grid": grid_data,
            "size": self.size,
            "words": words_data,
            "clues": {
                "across": across_clues,
                "down": down_clues
            }
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(crossword_data, f, indent=2, ensure_ascii=False)
            print(f"Crossword exported to {filename}")
        except Exception as e:
            print(f"Error exporting to JSON: {e}")

# Example usage and demonstration
def main():
    # Create crossword generator with smaller board
    generator = CrosswordGenerator(size=8)
    
    # Load from short_word_clues.json file
    word_clues = generator.load_from_json_file("short_word_clues.json")
    
    
    if generator.generate_crossword(word_clues, target_words=8):
        # Print the crossword
        generator.print_grid()
        generator.print_clues()
        generator.print_solution()
        
        # Export to JSON
        generator.export_to_json("generated_crossword.json")
    else:
        print("Failed to generate crossword with enough connected words")

if __name__ == "__main__":
    main()