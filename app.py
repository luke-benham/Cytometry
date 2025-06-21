# app.py
import streamlit as st
import pandas as pd
import database
import analysis

st.set_page_config(layout="wide", page_title="Loblaw Bio - Cytometry Analysis")

# --- App State Management ---
if 'db_initialized' not in st.session_state:
    st.session_state.db_initialized = False

# --- UI ---
st.title("📊 Cytometry Data Analysis for Loblaw Bio")
st.write("An interactive tool to analyze clinical trial immune cell data.")

# --- Sidebar for Data Management ---
with st.sidebar:
    st.header("Data Management")
    
    if st.button("Initialize/Reload Database from CSV", key="init_db"):
        with st.spinner("Loading data..."):
            conn = database.create_connection()
            database.create_tables(conn)
            message = database.load_data_from_csv(conn)
            conn.close()
            st.session_state.db_initialized = True
            st.success(message)

    if st.session_state.db_initialized:
        st.success("Database is ready.")
    else:
        st.warning("Database not initialized. Please load data.")

    # Part 1: Add/Remove Samples
    with st.expander("Manage Samples", expanded=False):
        
        # --- NEW: ADD SAMPLE FORM ---
        st.subheader("Add New Sample")
        with st.form("add_sample_form"):
            st.write("Enter details for the new sample. All fields are required.")
            
            # Group inputs into columns for better layout
            c1, c2 = st.columns(2)
            with c1:
                project = st.text_input("Project", "prj3")
                subject_id = st.text_input("Subject ID", "sbj3500")
                sample_id = st.text_input("Sample ID (must be unique)", "sample10500")
                age = st.number_input("Age", min_value=0, max_value=120, value=65)
                sex = st.selectbox("Sex", ["M", "F"])
                condition = st.selectbox("Condition", ["melanoma", "carcinoma", "healthy"])

            with c2:
                treatment = st.selectbox("Treatment", ["miraclib", "phauximab", "none"])
                response_options = ["", "yes", "no"]
                response = st.selectbox("Response", response_options, format_func=lambda x: "Not Applicable" if x == "" else x)
                sample_type = st.selectbox("Sample Type", ["PBMC", "WB"])
                time = st.number_input("Time From Treatment Start", min_value=0, value=0)
                
            st.subheader("Cell Counts")
            cc1, cc2, cc3, cc4, cc5 = st.columns(5)
            with cc1:
                b_cell = st.number_input("B-Cell", min_value=0, value=10000)
            with cc2:
                cd8_t_cell = st.number_input("CD8+ T-Cell", min_value=0, value=20000)
            with cc3:
                cd4_t_cell = st.number_input("CD4+ T-Cell", min_value=0, value=30000)
            with cc4:
                nk_cell = st.number_input("NK Cell", min_value=0, value=15000)
            with cc5:
                monocyte = st.number_input("Monocyte", min_value=0, value=18000)

            submitted = st.form_submit_button("Add Sample to Database")

            if submitted:
                # Basic validation
                if not all([project, subject_id, sample_id, age, sex, condition]):
                    st.error("Please fill all required metadata fields.")
                else:
                    sample_data = {
                        "project": project, "subject_id": subject_id, "age": age, "sex": sex, 
                        "condition": condition, "sample_id": sample_id, "treatment": treatment,
                        "response": response, "sample_type": sample_type, "time_from_treatment_start": time,
                        "b_cell": b_cell, "cd8_t_cell": cd8_t_cell, "cd4_t_cell": cd4_t_cell,
                        "nk_cell": nk_cell, "monocyte": monocyte
                    }
                    with st.spinner("Adding sample..."):
                        add_status = database.add_sample(sample_data)
                        if "Success" in add_status:
                            st.success(add_status)
                            st.rerun() # This is key to automatically updating the app
                        else:
                            st.error(add_status)

        st.divider()
        # --- REMOVE SAMPLE SECTION ---
        st.subheader("Remove Sample")
        remove_id = st.text_input("Sample ID to Remove", placeholder="e.g., sample00000", key="remove_id")
        if st.button("Remove Sample"):
            if remove_id:
                rows_deleted = database.remove_sample(remove_id)
                if rows_deleted > 0:
                    st.success(f"Removed sample '{remove_id}'.")
                    st.rerun() # Rerun to reflect the deletion
                else:
                    st.error(f"Sample ID '{remove_id}' not found.")
            else:
                st.warning("Please enter a Sample ID.")

# --- Main Page Content ---
if not st.session_state.db_initialized:
    st.info("Please initialize the database using the button in the sidebar to begin analysis.")
else:
    # Load data for all analyses
    full_data = database.get_full_dataset()

    # Part 2: Initial Analysis - Data Overview
    st.header("Part 2: Cell Population Frequency Overview")
    with st.spinner("Calculating frequencies..."):
        frequency_df = analysis.calculate_frequencies(full_data)
    
    st.write(f"This table shows the relative frequency of each cell population for **{full_data['sample_id'].nunique()}** samples.")
    st.dataframe(frequency_df)

    @st.cache_data
    def convert_df_to_csv(df):
        return df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="Download Frequency Data as CSV",
        data=convert_df_to_csv(frequency_df),
        file_name='cell_population_frequencies.csv',
        mime='text/csv',
    )
    st.markdown("---")

    # Part 3: Statistical Analysis - Responders vs. Non-responders
    st.header("Part 3: Miraclib Responder vs. Non-Responder Analysis (Melanoma)")
    st.write("Comparing cell population frequencies in melanoma patients treated with miraclib.")
    
    with st.spinner("Running statistical analysis..."):
        responder_freq_df, stats_df = analysis.compare_responders(full_data)
        boxplot_fig = analysis.create_boxplot(responder_freq_df)

    st.plotly_chart(boxplot_fig, use_container_width=True)
    
    st.subheader("Statistical Significance (Welch's t-test)")
    st.write("A t-test is used to compare the means of the two groups (responders vs. non-responders). A low p-value (typically < 0.05) suggests a significant difference between the groups.")
    
    def highlight_significant(s):
        return ['background-color: #90EE90']*len(s) if s['Significant (p<0.05)'] else ['']*len(s)

    st.dataframe(stats_df.style.apply(highlight_significant, axis=1))
    
    significant_pops = stats_df[stats_df['Significant (p<0.05)']]['Population'].tolist()
    if significant_pops:
        st.success(f"**Finding:** The relative frequencies of **{', '.join(significant_pops)}** are significantly different between responders and non-responders.")
    else:
        st.info("**Finding:** No cell populations showed a statistically significant difference between responders and non-responders at a p<0.05 threshold.")
    st.markdown("---")

    # Part 4: Data Subset Analysis
    st.header("Part 4: Data Subset Analysis")
    st.write("Analysis of baseline (Day 0) Melanoma PBMC samples from patients treated with Miraclib.")
    
    with st.spinner("Analyzing data subset..."):
        subset_stats = analysis.get_subset_stats(full_data)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Samples per Project")
        st.dataframe(subset_stats['project_counts'])
    with col2:
        st.subheader("Subject Response")
        st.dataframe(subset_stats['responder_counts'])
    with col3:
        st.subheader("Subject Sex")
        st.dataframe(subset_stats['gender_counts'])