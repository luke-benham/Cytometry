# Loblaw Bio - Cytometry Data Analysis Tool

This project is a Python-based interactive web application designed to help scientists at Loblaw Bio analyze clinical trial cytometry data. It provides functionality for data management, exploratory analysis, statistical comparison, and data subsetting.

## Deployed Application

A live version of this application can be accessed here:
**[https://luke-benham-cytometry-app-ygdphs.streamlit.app/](https://luke-benham-cytometry-app-ygdphs.streamlit.app/)** 

## Features

- **Database Management**: Initializes a local SQLite database and loads data from a CSV file. Users can easily rerun the loading process to update the data.
- **Data Overview**: Generates a summary table of the relative frequency (%) of five immune cell populations for every sample.
- **Statistical Analysis**: Compares cell frequencies between treatment responders and non-responders for a specific cohort (Melanoma patients on Miraclib).
- **Interactive Visualization**: Displays an interactive boxplot to visually compare responder groups.
- **Significance Testing**: Automatically performs a Welch's t-test to identify cell populations with statistically significant differences and highlights the results.
- **Subset Analysis**: Allows for quick analysis of specific data subsets, such as baseline samples for a given treatment and condition.

## Database Schema Design

The database uses SQLite and is designed with two primary tables to achieve a degree of normalization, which enhances scalability and data integrity.

- **`subjects` Table**: Stores metadata that is unique to each subject, regardless of how many samples they provide.
  - `subject_id` (PRIMARY KEY)
  - `project`
  - `age`
  - `sex`
  - `condition`
- **`samples` Table**: Stores data for each individual sample, linking back to the subject.
  - `sample_id` (PRIMARY KEY)
  - `subject_id` (FOREIGN KEY to `subjects.subject_id`)
  - `treatment`, `response`, `sample_type`, `time_from_treatment_start`
  - Cell counts: `b_cell`, `cd8_t_cell`, `cd4_t_cell`, `nk_cell`, `monocyte`

### Rationale and Scalability

This two-table schema was chosen as a balance between full normalization and simplicity for this specific dataset.

- **Why not a single flat table?** A single table would repeat subject metadata (age, sex, condition) for every sample from that subject. This is redundant and can lead to update anomalies.
- **How does this scale?**
  - **Hundreds of Projects**: This schema handles new projects easily, as `project` is just an attribute of a `subject`. No schema changes are needed.
  - **Thousands of Samples**: The relational model is efficient. Queries can join the tables on the indexed `subject_id` key, which remains fast even with millions of rows in the `samples` table.
  - **Various Analytics**: For more complex analytics (e.g., adding new cell types or new metadata), this schema is extensible:
    - **New Cell Types**: Instead of adding more columns to `samples`, a more normalized approach would be a `CellCounts` table (`sample_id`, `cell_type`, `count`). This would allow adding infinite new cell types without schema changes.
    - **New Metadata**: Additional metadata could be added as new columns to the `subjects` or `samples` tables, or linked via new tables (e.g., a `Treatments` table with details about each drug).

This design ensures that the most common queries (filtering by subject or sample properties) are efficient, while providing a clear path to further normalization as the project's complexity grows.

## Code Structure

The project is organized into three main Python files to separate concerns:

- **`database.py`**: Handles all database connection, table creation, and data loading/querying logic. It acts as the data access layer.
- **`analysis.py`**: Contains all the business logic for data analysis, including frequency calculations, statistical tests, and data preparation for plots. This keeps the core computations separate from the UI.
- **`app.py`**: The main Streamlit application file. It controls the user interface, handles user input, and calls functions from `database.py` and `analysis.py` to display results. This separation makes the code cleaner and easier to maintain.

## How to Run the Application Locally

1.  **Prerequisites**:
    - Python 3.8+
    - Git

2.  **Clone the Repository**:
    ```bash
    git clone <your-repository-url>
    cd <repository-name>
    ```

3.  **Set Up Virtual Environment**:
    ```bash
    # Create the environment
    python -m venv .venv

    # Activate it (macOS/Linux)
    source .venv/bin/activate

    # Activate it (Windows PowerShell)
    .\.venv\Scripts\Activate.ps1
    ```

4.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Run the Streamlit App**:
    ```bash
    streamlit run app.py
    ```
    The application will open in your default web browser.

6.  **Using the App**:
    - Click the **"Initialize/Load Database from CSV"** button in the sidebar to load the data.
    - The analyses will automatically run and display on the main page.
    - Use the sidebar options to manage samples. The page will update accordingly upon refresh.
    - The sidebar is extendable for easier data entry. 