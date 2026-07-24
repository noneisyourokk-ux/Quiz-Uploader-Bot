import json

def parse_txt(text_content: str) -> list:
    """Parses TXT files into quiz dicts."""
    quizzes = []
    raw_blocks = text_content.strip().split("\n\n")
    
    for block in raw_blocks:
        lines = [line.strip() for line in block.split("\n") if line.strip()]
        if not lines:
            continue
            
        question = lines[0]
        options = []
        correct_option_id = None
        explanation = ""
        
        for line in lines[1:]:
            if line.startswith("-- Explanation:"):
                explanation = line.replace("-- Explanation:", "").strip()
            elif line.startswith("* -") or line.startswith("*-"):
                correct_option_id = len(options)
                options.append(line.lstrip("*- ").strip())
            elif line.startswith("-"):
                options.append(line.lstrip("- ").strip())
                
        if question and options and correct_option_id is not None:
            quizzes.append({
                "question": question,
                "options": options,
                "correct_option_id": correct_option_id,
                "explanation": explanation
            })
            
    return quizzes

def parse_file_content(content_str: str, filename: str) -> list:
    """Detects file type and parses content."""
    if filename.endswith(".json"):
        data = json.loads(content_str)
        return data if isinstance(data, list) else [data]
    else:
        return parse_txt(content_str)
