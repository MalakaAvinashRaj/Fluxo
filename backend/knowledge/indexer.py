# import
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from typing import List
from services.rag_service import index



# chunk the text by h2 headings
def chunk_by_h2(text: str) -> List[str]:
    chunks = text.split("\n## ")
    chunks = ["## " + chunk for chunk in chunks if chunk.strip()]
    chunks = chunks[1:]
    return chunks

# chunk the text by h3 headings
def chunk_by_h3(text: str) -> List[str]:
    chunks = text.split("\n### ")
    chunks = ["### " + chunk for chunk in chunks if chunk.strip()]
    chunks = chunks[1:]
    return chunks

# index the chunks by file
def index_chunks():
    files = pathlib.Path("knowledge/sources/").glob("*.md")
    for file in files:
        if "error_fixes" in file.name:
            chunks = chunk_by_h3(file.read_text())
        else:
            chunks = chunk_by_h2(file.read_text())
            
        ids = [f"{file.name}-{i}" for i in range(len(chunks))]
        
        index(chunks, ids);
        print(f"Indexed {file.name} with {len(chunks)} chunks")
            

if __name__ == "__main__":
    index_chunks()
    


    

        