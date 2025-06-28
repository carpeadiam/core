import json
import random
import re
import struct
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Word:
    text: str
    clue: str
    row: int
    col: int
    direction: str  # 'across' or 'down'
    number: int = 0

class CrosswordGenerator:
    def __init__(self, size: int = 10):
        self.size = size
        self.grid = [[' ' for _ in range(size)] for _ in range(size)]
        self.placed_words: List[Word] = []
        self.number_grid = [[0 for _ in range(size)] for _ in range(size)]
        
    def validate_word(self, word: str) -> bool:
        """Check if word contains only letters (no numbers, spaces, or special characters)"""
        return bool(re.match(r'^[A-Za-z]+$', word))
    
    def load_from_json_file(self, filename: str) -> Dict[str, List[str]]:
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
                    print(f"Warning: Skipping invalid word '{word}'")
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
    
    def place_word(self, word: str, row: int, col: int, direction: str, clue: str):
        """Place a word on the grid"""
        if direction == 'across':
            for i, letter in enumerate(word):
                self.grid[row][col + i] = letter
        else:  # down
            for i, letter in enumerate(word):
                self.grid[row + i][col] = letter
        
        word_obj = Word(word, clue, row, col, direction)
        self.placed_words.append(word_obj)
    
    def assign_numbers(self):
        """Improved numbering logic that follows standard crossword conventions"""
        # Clear number grid
        self.number_grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        
        # Collect all starting positions that need numbers
        numbered_positions: Set[Tuple[int, int]] = set()
        
        for word in self.placed_words:
            numbered_positions.add((word.row, word.col))
        
        # Sort positions by row then column (top to bottom, left to right)
        sorted_positions = sorted(numbered_positions, key=lambda pos: (pos[0], pos[1]))
        
        # Assign numbers sequentially
        position_to_number = {}
        current_number = 1
        
        for pos in sorted_positions:
            position_to_number[pos] = current_number
            self.number_grid[pos[0]][pos[1]] = current_number
            current_number += 1
        
        # Update word numbers
        for word in self.placed_words:
            word.number = position_to_number[(word.row, word.col)]
        
        # Debug output
        print("\nNumber assignments:")
        for word in sorted(self.placed_words, key=lambda w: w.number):
            print(f"  {word.number}. {word.text} ({word.direction}) at ({word.row},{word.col})")
    
    def find_intersections(self, word: str, placed_word: Word) -> List[Tuple[int, int, int, int, str]]:
        """Find possible intersections between a word and a placed word"""
        intersections = []
        
        for i, letter1 in enumerate(word):
            for j, letter2 in enumerate(placed_word.text):
                if letter1 == letter2:
                    if placed_word.direction == 'across':
                        # New word goes down, intersecting with across word
                        new_row = placed_word.row - i
                        new_col = placed_word.col + j
                        if (new_row >= 0 and new_row + len(word) <= self.size and 
                            new_col >= 0 and new_col < self.size):
                            intersections.append((new_row, new_col, i, j, 'down'))
                    else:
                        # New word goes across, intersecting with down word
                        new_row = placed_word.row + j
                        new_col = placed_word.col - i
                        if (new_col >= 0 and new_col + len(word) <= self.size and 
                            new_row >= 0 and new_row < self.size):
                            intersections.append((new_row, new_col, i, j, 'across'))
        
        return intersections
    
    def generate_crossword(self, word_clues: Dict[str, List[str]], target_words: int = 8) -> bool:
        """Generate a crossword puzzle with connected words only"""
        if not word_clues:
            print("No valid words provided")
            return False
        
        # Load secondary word file
        word_clues2 = self.load_from_json_file("short_word_clues2.json")
        
        # Reset grid
        self.grid = [[' ' for _ in range(self.size)] for _ in range(self.size)]
        self.placed_words = []
        self.number_grid = [[0 for _ in range(self.size)] for _ in range(self.size)]
        
        # Prepare word list mixing words from both files
        word_list = self._prepare_word_list(word_clues, word_clues2, target_words)
        
        if not word_list:
            print("No words with clues found")
            return False
        
        # Place first word in center
        first_word, first_clue = word_list[0]
        start_row = self.size // 2
        start_col = (self.size - len(first_word)) // 2
        
        # Ensure first word fits
        start_col = max(0, min(start_col, self.size - len(first_word)))
        self.place_word(first_word, start_row, start_col, 'across', first_clue)
        
        placed_count = 1
        max_attempts = 200
        
        # Place remaining words with intersections only
        for word, clue in word_list[1:]:
            if placed_count >= target_words:
                break
                
            placed = False
            attempts = 0
            
            while attempts < max_attempts and not placed:
                # Try intersecting with existing words
                existing_words = self.placed_words.copy()
                random.shuffle(existing_words)
                
                for placed_word in existing_words:
                    intersections = self.find_intersections(word, placed_word)
                    if intersections:
                        random.shuffle(intersections)
                        
                        for row, col, word_idx, placed_idx, direction in intersections:
                            if self.can_place_word(word, row, col, direction):
                                self.place_word(word, row, col, direction, clue)
                                placed_count += 1
                                placed = True
                                break
                    
                    if placed:
                        break
                
                attempts += 1
            
            if not placed:
                print(f"Could not place word '{word}' with intersection")
        
        # Assign numbers after all words are placed
        self.assign_numbers()
        
        print(f"Successfully placed {placed_count} connected words")
        return placed_count >= 7
    
    def _prepare_word_list(self, word_clues1: Dict[str, List[str]], 
                         word_clues2: Dict[str, List[str]], 
                         target_words: int) -> List[Tuple[str, str]]:
        """Prepare mixed word list from both sources"""
        words1 = list(word_clues1.items())
        random.shuffle(words1)
        
        words2 = list(word_clues2.items()) if word_clues2 else []
        if words2:
            random.shuffle(words2)
        
        word_list = []
        word2_index = 0
        
        for i, (word, clues) in enumerate(words1):
            if not clues:
                continue
                
            # Every 4th word comes from second file if available
            if (i + 1) % 2 == 0 and words2 and word2_index < len(words2):
                word2, clues2 = words2[word2_index]
                if clues2:
                    word_list.append((word2, random.choice(clues2)))
                    word2_index += 1
                    continue
            
            word_list.append((word, random.choice(clues)))
        
        # Add remaining words from second file if needed
        while word2_index < len(words2) and len(word_list) < target_words * 2:
            word2, clues2 = words2[word2_index]
            if clues2:
                word_list.append((word2, random.choice(clues2)))
            word2_index += 1
        
        return word_list
    
    def print_grid(self):
        """Print the crossword grid with numbers"""
        print("\n" + "="*60)
        print("CROSSWORD PUZZLE")
        print("="*60)
        
        # Print column numbers
        print("   ", end="")
        for i in range(self.size):
            print(f"{i:2d}", end=" ")
        print()
        
        # Print grid with row numbers and word numbers
        for i in range(self.size):
            print(f"{i:2d} ", end="")
            for j in range(self.size):
                cell = self.grid[i][j]
                number = self.number_grid[i][j]
                
                if cell == ' ':
                    print(" ■", end=" ")
                else:
                    if number > 0:
                        print(f"{number:2d}", end="")
                        print(cell.lower(), end=" ")
                    else:
                        print(f" {cell.lower()}", end=" ")
            print()
        
        print("\n" + "="*60)
    
    def print_clues(self):
        """Print the clues organized by direction and properly numbered"""
        if not self.placed_words:
            print("No words placed yet!")
            return
        
        across_words = sorted([w for w in self.placed_words if w.direction == 'across'], 
                            key=lambda x: x.number)
        down_words = sorted([w for w in self.placed_words if w.direction == 'down'], 
                          key=lambda x: x.number)
        
        print("\nACROSS:")
        print("-" * 40)
        for word in across_words:
            print(f"{word.number:2d}. {word.clue}")
        
        print("\nDOWN:")
        print("-" * 40)
        for word in down_words:
            print(f"{word.number:2d}. {word.clue}")
    
    def print_solution(self):
        """Print the solution with word positions"""
        print("\nSOLUTION:")
        print("="*60)
        for word in sorted(self.placed_words, key=lambda x: x.number):
            print(f"{word.number:2d}. {word.text} ({word.direction}) - Row {word.row}, Col {word.col}")
        print()
    
    def export_to_json(self, filename: str = "crossword_puzzle.json"):
        """Export the crossword puzzle to JSON format with correct numbering"""
        if not self.placed_words:
            print("No crossword to export!")
            return
        
        # Create grid representation
        grid_data = []
        for i in range(self.size):
            row_data = []
            for j in range(self.size):
                cell_info = {
                    "letter": self.grid[i][j] if self.grid[i][j] != ' ' else None,
                    "number": self.number_grid[i][j] if self.number_grid[i][j] > 0 else None,
                    "black": self.grid[i][j] == ' '
                }
                row_data.append(cell_info)
            grid_data.append(row_data)
        
        # Create words data sorted by number
        words_data = []
        for word in sorted(self.placed_words, key=lambda x: x.number):
            words_data.append({
                "word": word.text,
                "clue": word.clue,
                "row": word.row,
                "col": word.col,
                "direction": word.direction,
                "number": word.number
            })
        
        # Create clues data properly ordered
        across_clues = {}
        down_clues = {}
        
        for word in sorted(self.placed_words, key=lambda x: x.number):
            if word.direction == 'across':
                across_clues[str(word.number)] = word.clue
            else:
                down_clues[str(word.number)] = word.clue
        
        crossword_data = {
            "metadata": {
                "title": "Generated Crossword",
                "author": "Crossword Generator",
                "size": self.size,
                "created": datetime.now().isoformat()
            },
            "grid": grid_data,
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
        
    def export_to_puz(self, filename: str = "crossword.puz", title: str = "Generated Crossword", 
                    author: str = "Crossword Generator", copyright: str = "") -> bool:
        """Export to .puz format with correct structure and checksums"""
        if not self.placed_words:
            print("No crossword to export!")
            return False
        
        try:
            # Build solution and grid strings
            solution = []
            grid = []
            
            for row in self.grid:
                for cell in row:
                    if cell == ' ':
                        solution.append('.')
                        grid.append('.')
                    else:
                        solution.append(cell)
                        grid.append('-')
            
            solution_str = ''.join(solution)
            grid_str = ''.join(grid)
            
            # Get ALL words sorted by number (this is the key fix)
            all_words = sorted(self.placed_words, key=lambda x: x.number)
            
            # Build clues in numerical order
            clues = []
            for word in all_words:
                clues.append(word.clue)
            
            # Convert strings to bytes
            title_bytes = title.encode('latin-1', errors='replace')[:50]
            author_bytes = author.encode('latin-1', errors='replace')[:50]
            copyright_bytes = copyright.encode('latin-1', errors='replace')[:50]
            
            # Build the file
            data = bytearray()
            
            # Header
            data.extend(b'ACROSS&DOWN\x00')  # File signature
            data.extend(b'\x00\x00')  # CIB checksum (placeholder)
            data.extend(b'ICHEATED')  # Masked low checksums
            data.extend(b'\x00\x00\x00\x00')  # Masked high checksums
            data.extend(b'\x31\x12')  # Version (0x1231 = 1.3)
            data.extend(b'\x00\x00')  # Reserved1C
            data.extend(b'\x00\x00')  # Scrambled checksum
            data.extend(b'\x00' * 12)  # Reserved1E
            
            # Puzzle dimensions and counts
            data.append(self.size)  # Width
            data.append(self.size)  # Height
            data.extend(struct.pack('<H', len(clues)))  # Number of clues
            data.extend(struct.pack('<H', 1))  # Puzzle type (1 = Normal)
            data.extend(struct.pack('<H', 0))  # Solution state (0 = unsolved)
            
            # Solution and grid
            data.extend(solution_str.encode('latin-1'))
            data.extend(grid_str.encode('latin-1'))
            
            # Strings
            data.extend(title_bytes + b'\x00')
            data.extend(author_bytes + b'\x00')
            data.extend(copyright_bytes + b'\x00')
            
            # Clues (now in correct numerical order)
            for clue in clues:
                clue_bytes = clue.encode('latin-1', errors='replace')
                data.extend(clue_bytes + b'\x00')
            
            # Notes (empty)
            data.extend(b'\x00')
            
            # Calculate checksums
            def cksum_region(data: bytearray, start: int, length: int, cksum: int = 0) -> int:
                """Calculate checksum for a region of data"""
                for i in range(start, start + length):
                    if i < len(data):
                        cksum = (cksum >> 1) | ((cksum & 1) << 15)
                        cksum = (cksum + data[i]) & 0xFFFF
                return cksum
            
            # Calculate the primary checksum (CIB checksum)
            cksum = cksum_region(data, 0x2C, len(data) - 0x2C)
            
            # Update CIB checksum
            struct.pack_into('<H', data, 0x0E, cksum)
            
            # Calculate overall file checksum for header
            file_cksum = cksum_region(data, 0x2C, 8)
            struct.pack_into('<H', data, 0x00, file_cksum)
            
            # Write to file
            with open(filename, 'wb') as f:
                f.write(data)
            
            print(f"Successfully exported to {filename}")
            return True
            
        except Exception as e:
            print(f"Error exporting .puz file: {e}")
            return False
def main():
    # Create crossword generator
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

if __name__ == "__main__":
    main()