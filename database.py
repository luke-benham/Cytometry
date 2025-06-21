# database.py

import sqlite3
import pandas as pd

DB_FILE = "trial_data.db"

def create_connection():
    """Create a database connection to the SQLite database."""
    conn = None
    try:
        conn = sqlite3.connect(DB_FILE, timeout=10) # Added timeout for robustness
    except sqlite3.Error as e:
        print(e)
    return conn

def create_tables(conn):
    """Create tables from the schema."""
    subject_table_sql = """
    CREATE TABLE IF NOT EXISTS subjects (
        subject_id TEXT PRIMARY KEY,
        project TEXT NOT NULL,
        age INTEGER,
        sex TEXT,
        condition TEXT
    );
    """
    sample_table_sql = """
    CREATE TABLE IF NOT EXISTS samples (
        sample_id TEXT PRIMARY KEY,
        subject_id TEXT NOT NULL,
        treatment TEXT,
        response TEXT,
        sample_type TEXT,
        time_from_treatment_start INTEGER,
        b_cell INTEGER,
        cd8_t_cell INTEGER,
        cd4_t_cell INTEGER,
        nk_cell INTEGER,
        monocyte INTEGER,
        FOREIGN KEY (subject_id) REFERENCES subjects (subject_id)
    );
    """
    try:
        c = conn.cursor()
        c.execute(subject_table_sql)
        c.execute(sample_table_sql)
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error creating tables: {e}")

def load_data_from_csv(conn, csv_filepath='data/cell-count.csv'):
    """Load data from CSV file into the SQLite database."""
    try:
        df = pd.read_csv(csv_filepath)
        
        # Prepare subjects data (unique subjects)
        subjects_df = df[['subject', 'project', 'age', 'sex', 'condition']].drop_duplicates(subset=['subject'])
        subjects_df = subjects_df.rename(columns={'subject': 'subject_id'})
        
        # Prepare samples data
        samples_df = df.rename(columns={'sample': 'sample_id', 'subject': 'subject_id'})
        samples_df = samples_df.drop(columns=['project', 'age', 'sex', 'condition'])

        subjects_df.to_sql('subjects', conn, if_exists='replace', index=False)
        samples_df.to_sql('samples', conn, if_exists='replace', index=False)
        conn.commit()
        return f"Successfully loaded {len(df)} rows from {csv_filepath}."
    except Exception as e:
        return f"Error loading data: {e}"

def get_full_dataset():
    """Query and join tables to get the full dataset as a DataFrame."""
    conn = create_connection()
    if conn is None:
        return pd.DataFrame()
        
    query = """
    SELECT
        s.*,
        sub.project,
        sub.age,
        sub.sex,
        sub.condition
    FROM samples s
    JOIN subjects sub ON s.subject_id = sub.subject_id
    """
    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        print(f"Error fetching data: {e}")
        df = pd.DataFrame()
    finally:
        if conn:
            conn.close()
    return df

def remove_sample(sample_id):
    """Remove a sample by its ID."""
    conn = create_connection()
    if not conn: return 0
    sql = 'DELETE FROM samples WHERE sample_id = ?'
    cur = conn.cursor()
    try:
        cur.execute(sql, (sample_id,))
        conn.commit()
        rows_deleted = cur.rowcount
    except sqlite3.Error as e:
        print(f"Error removing sample: {e}")
        rows_deleted = 0
    finally:
        if conn:
            conn.close()
    return rows_deleted

# --- NEW FUNCTION TO ADD A SAMPLE ---
def add_sample(data):
    """
    Adds a new subject (if they don't exist) and a new sample to the database.
    
    Args:
        data (dict): A dictionary containing all necessary columns for subjects and samples.
    
    Returns:
        str: A message indicating success or failure.
    """
    conn = create_connection()
    if not conn: return "Error: Could not connect to the database."
    
    try:
        cur = conn.cursor()
        
        # Step 1: Add the subject. 'INSERT OR IGNORE' prevents errors if the subject already exists.
        # This is an atomic and safe way to handle existing subjects.
        subject_sql = ''' INSERT OR IGNORE INTO subjects(subject_id, project, age, sex, condition)
                          VALUES(?,?,?,?,?) '''
        cur.execute(subject_sql, (data['subject_id'], data['project'], data['age'], data['sex'], data['condition']))
        
        # Step 2: Add the sample. This will fail if sample_id is not unique.
        sample_sql = ''' INSERT INTO samples(sample_id, subject_id, treatment, response, sample_type, 
                                            time_from_treatment_start, b_cell, cd8_t_cell, cd4_t_cell, 
                                            nk_cell, monocyte)
                         VALUES(?,?,?,?,?,?,?,?,?,?,?) '''
        cur.execute(sample_sql, (
            data['sample_id'], data['subject_id'], data['treatment'], data['response'], 
            data['sample_type'], data['time_from_treatment_start'], data['b_cell'], 
            data['cd8_t_cell'], data['cd4_t_cell'], data['nk_cell'], data['monocyte']
        ))
        
        conn.commit()
        return f"Success: Sample '{data['sample_id']}' for subject '{data['subject_id']}' has been added."

    except sqlite3.IntegrityError:
        # This error is raised if the sample_id (PRIMARY KEY) already exists.
        return f"Error: Sample ID '{data['sample_id']}' already exists. Please use a unique ID."
    except Exception as e:
        return f"An unexpected error occurred: {e}"
    finally:
        if conn:
            conn.close()