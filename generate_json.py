import json
import logging
from typing import List, Dict, Optional

# Set up logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_scripture_reference(reference: str) -> Dict[str, str]:
    """Parse a scripture reference into book, chapters, and verses."""
    if ':' in reference:
        chapters, verses = reference.split(':')
        return {"chapters": chapters, "verses": verses}
    return {"chapters": reference, "verses": "all"}

def create_reading(book: str, reference: str) -> Dict:
    """Create a reading dictionary from book and reference."""
    reference_data = parse_scripture_reference(reference)
    return {
        "book": book,
        "chapters": reference_data["chapters"],
        "verses": reference_data["verses"]
    }

def parse_text_to_json(file_path: str) -> str:
    """Parse a Bible reading plan text file into JSON format."""
    with open(file_path, 'r') as f:
        lines = f.readlines()

    logging.info(f"Read {len(lines)} lines from the file.")

    result = []
    current_period = ""
    
    for line in lines:
        # Remove leading/trailing whitespace and skip empty lines
        line = line.strip()
        if not line:
            continue
            
        # Handle lines with multiple spaces between words
        parts = [part for part in line.split() if part]
        
        if not parts:  # Skip if line is all whitespace
            continue
            
        if not parts[0].lower() == 'day':  # This is a period header
            current_period = line.strip()
            logging.info(f"New period detected: {current_period}")
            continue
        
        try:
            # Ensure we have at least "Day X Book Chapter" format
            if len(parts) < 4:
                logging.warning(f"Skipping malformed line: {line}")
                continue
                
            day_number = int(parts[1])
            
            # Initialize readings
            first_reading = None
            second_reading = None
            poem = None
            
            i = 2  # Start after "Day X"
            
            # Process first reading
            if i < len(parts):
                first_reading = create_reading(parts[i], parts[i + 1])
                i += 2
            
            # Process second reading or poem
            if i < len(parts):
                if parts[i].lower() in ['psalm', 'psalms', 'proverb', 'proverbs']:
                    poem = create_reading(parts[i], parts[i + 1])
                else:
                    second_reading = create_reading(parts[i], parts[i + 1])
                    # If there's still more, it must be a poem
                    if i + 2 < len(parts):
                        poem = create_reading(parts[i + 2], parts[i + 3])
            
            day_data = {
                "day": day_number,
                "period": current_period,
                "first_reading": first_reading,
                "second_reading": second_reading if second_reading else "none",
                "poem": poem
            }
            
            result.append(day_data)
            logging.debug(f"Processed Day {day_number}: {day_data}")
            
        except Exception as e:
            logging.error(f"Error processing line '{line}': {str(e)}")
            continue

    # Convert to JSON with proper formatting
    return json.dumps(result, indent=4)

def save_json_to_file(json_str: str, output_path: str) -> None:
    """Save the JSON string to a file."""
    with open(output_path, 'w') as f:
        f.write(json_str)
    logging.info(f"Saved JSON output to {output_path}")

# Example usage:
if __name__ == "__main__":
    try:
        input_file = 'plan.txt'
        output_file = 'reading_plan.json'
        
        json_output = parse_text_to_json(input_file)
        save_json_to_file(json_output, output_file)
        
    except FileNotFoundError:
        logging.error(f"Could not find input file: {input_file}")
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")