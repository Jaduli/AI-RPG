import sqlite3
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import os

DB_PATH = "/app/data/memory.db"

"""
Sentence tranformer model for semantic search:
https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2
"""
model = SentenceTransformer("all-MiniLM-L6-v2")

"""
Connect to database.
"""
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

"""
Creates a SQLite table for storing memories.
"""
def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS memories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            story_id INTEGER NOT NULL,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Add index for more efficient memory search
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_story_id_created_at 
        ON memories(story_id, created_at DESC)
    """)
    conn.commit()
    conn.close()

"""
Gets the path for where a FAISS index for given story_id is stored on disk.
"""
def get_faiss_path(story_id):
    return f"/app/data/faiss_{story_id}.index"


"""
Loads FAISS index from path or creates a new one if missing.
"""
def load_index(story_id):
    path = get_faiss_path(story_id)

    if os.path.exists(path):
        index = faiss.read_index(path)

        # Make sure index supports ID mapping
        if not isinstance(index, faiss.IndexIDMap):
            index = faiss.IndexIDMap(index)

        return index

    # Create new index if it doesn't exist
    dimension = 384
    base_index = faiss.IndexFlatL2(dimension)
    return faiss.IndexIDMap(base_index)


"""
Saves index based on path.
"""
def save_index(index, story_id):
    faiss.write_index(index, get_faiss_path(story_id))

"""
Adds a new memory into the database. Returns generated ID for memory.
"""
def add_memory(story_id, content):
    conn = get_db()

    # Pass parameters to prevent SQL injection
    cursor = conn.execute(
        "INSERT INTO memories (story_id, content) VALUES (?, ?)",
        (story_id, content)
    )
    conn.commit()
    memory_id = cursor.lastrowid
    conn.close()
    return memory_id

"""
Gets stored memories based on story ID. Returns a list of all memories.
"""
def get_memories(story_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT content FROM memories WHERE story_id = ? ORDER BY created_at DESC",
        (story_id,)
    ).fetchall()
    conn.close()
    return [row["content"] for row in rows]

"""
Gets most recent memories based on story ID up to a specified limit.
Skip could be used to skip a number of most recent memories, e.g. if content is included in summary.
Skip is currently unused as story consistency was found to be better without it in testing. 
"""
def get_recent_memories(story_id, limit=2, skip=0):
    conn = get_db()
    rows = conn.execute(
        "SELECT content FROM memories WHERE story_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (story_id, limit, skip)
    ).fetchall()
    conn.close()
    return [row["content"] for row in rows]

"""
Gets a number of random memories for a story.
"""
def get_random_memories(story_id, limit=2):
    conn = get_db()
    rows = conn.execute(
        "SELECT content FROM memories WHERE story_id = ? ORDER BY RANDOM() LIMIT ?",
        (story_id, limit)
    ).fetchall()
    conn.close()
    return [row["content"] for row in rows]

"""
Embeds text into a numeric vector, used for similarity search.
"""
def embed(text):
    return model.encode(text).astype("float32")

"""
Returns the number of stored memories for a story.
"""
def count_memories(story_id):
    conn = get_db()
    count = conn.execute(
        "SELECT COUNT(*) AS count FROM memories WHERE story_id = ?",
        (story_id,)
    ).fetchone()["count"]
    conn.close()
    return int(count)

"""
Removes the least relevant memory for a story based on text similarity.
"""
def remove_least_relevant_memory(story_id, content):
    conn = get_db()
    rows = conn.execute(
        "SELECT id, content FROM memories WHERE story_id = ? ORDER BY created_at DESC",
        (story_id,)
    ).fetchall()
    conn.close()

    if not rows:
        return None

    index = load_index(story_id)

    if index.ntotal == 0:
        return None

    query_embedding = embed(content)
    vector = query_embedding.reshape(1, -1)
    distances, indices = index.search(vector, len(rows))

    candidate_ids = [int(i) for i in indices[0] if i != -1]
    if not candidate_ids:
        return None

    # The last hit is the least similar memory in the FAISS result ordering.
    least_relevant_id = candidate_ids[-1]

    conn = get_db()
    conn.execute("DELETE FROM memories WHERE id = ?", (least_relevant_id,))
    conn.commit()
    conn.close()

    # Rebuild FAISS index to keep it consistent with SQLite.
    rebuild_index(story_id)
    return least_relevant_id

"""
Rebuilds the FAISS index for a story from the current SQLite memories.
"""
def rebuild_index(story_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT id, content FROM memories WHERE story_id = ? ORDER BY created_at ASC",
        (story_id,)
    ).fetchall()
    conn.close()

    index = faiss.IndexIDMap(faiss.IndexFlatL2(384))

    for row in rows:
        vector = embed(row["content"]).reshape(1, -1)
        ids = np.array([row["id"]], dtype="int64")
        index.add_with_ids(vector, ids)

    save_index(index, story_id)

"""
Saves content and index of memory to database. Returns ID of added memory.
A maximum of 70 memories are stored per story. If limit is exceeded, the 
least relevant memory is removed.
"""
def create_memory(story_id, content):
    while count_memories(story_id) >= 70:
        remove_least_relevant_memory(story_id, content)

    # Save to SQLite
    memory_id = add_memory(story_id, content)

    # Embed
    embedding = embed(content)
    vector = embedding.reshape(1, -1)
    ids = np.array([memory_id]).astype("int64")

    # Load story-specific index
    index = load_index(story_id)

    # Add vector
    index.add_with_ids(vector, ids)

    # Save index
    save_index(index, story_id)

    return memory_id

"""
Seaches the database for for most similar embedded memories.
top_k determines how many matches are returned.
"""
def search_memories(story_id, query_embedding, top_k=2):
    index = load_index(story_id)

    if index.ntotal == 0:
        return []

    vector = query_embedding.reshape(1, -1)
    distances, indices = index.search(vector, top_k)

    # Return indeces for most matching stored memories
    # Ignores missing memories (-1) e.g. when none have been created
    return [int(i) for i in indices[0] if i != -1]

"""
Gets relevant memories for current story content.
Returns a list with top_k number of stored memories.
"""
def get_relevant_memories(content, story_id, top_k=2):
    query_embedding = embed(content)

    # Search the for most similar memories
    ids = search_memories(story_id, query_embedding, top_k)

    if not ids:
        return []

    conn = get_db()

    # Get memories and their content from database
    rows = conn.execute(
        f"""
        SELECT id, content FROM memories 
        WHERE id IN ({','.join(['?']*len(ids))})
        """,
        ids
    ).fetchall()
    conn.close()

    # Format memories
    row_map = {row["id"]: row["content"] for row in rows}

    # Return memory content while preserving order
    return [row_map[i] for i in ids if i in row_map]