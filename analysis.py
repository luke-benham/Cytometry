# analysis.py
import pandas as pd
import plotly.express as px
from scipy.stats import ttest_ind

CELL_POPULATIONS = ['b_cell', 'cd8_t_cell', 'cd4_t_cell', 'nk_cell', 'monocyte']

def calculate_frequencies(df):
    """Calculates total counts and relative frequencies for each cell population."""
    df_copy = df.copy()
    df_copy['total_count'] = df_copy[CELL_POPULATIONS].sum(axis=1)
    
    # Melt dataframe from wide to long format
    long_df = pd.melt(
        df_copy, 
        id_vars=['sample_id', 'total_count'], 
        value_vars=CELL_POPULATIONS,
        var_name='population',
        value_name='count'
    )
    
    # Calculate percentage and handle division by zero
    long_df['percentage'] = long_df.apply(
        lambda row: (row['count'] / row['total_count'] * 100) if row['total_count'] > 0 else 0,
        axis=1
    )
    long_df = long_df.rename(columns={'sample_id': 'sample'})
    return long_df[['sample', 'total_count', 'population', 'count', 'percentage']]

def compare_responders(df):
    """
    Filters data for Melamona/Miraclib/PBMC and compares responders vs non-responders.
    """
    # Filter data
    filtered_df = df[
        (df['condition'] == 'melanoma') &
        (df['treatment'] == 'miraclib') &
        (df['sample_type'] == 'PBMC') &
        (df['response'].isin(['yes', 'no']))
    ].copy()
    
    # Calculate frequencies for the filtered data. This returns a df with a 'sample' column.
    freq_df = calculate_frequencies(filtered_df)
    
    # --- THIS IS THE CORRECTED LINE ---
    # Merge the frequency data with the original response data.
    # Use left_on='sample' for freq_df and right_on='sample_id' for the main df.
    full_freq_df = pd.merge(
        freq_df, 
        df[['sample_id', 'response']],  # Correctly select 'sample_id'
        left_on='sample', 
        right_on='sample_id'
    ).drop(columns='sample_id') # Drop the redundant column after merge
    
    # --- THE REST OF THE FUNCTION REMAINS THE SAME ---
    
    # Perform t-test for each population
    results = []
    for pop in CELL_POPULATIONS:
        pop_data = full_freq_df[full_freq_df['population'] == pop]
        responders = pop_data[pop_data['response'] == 'yes']['percentage']
        non_responders = pop_data[pop_data['response'] == 'no']['percentage']
        
        if len(responders) > 1 and len(non_responders) > 1:
            t_stat, p_value = ttest_ind(responders, non_responders, equal_var=False, nan_policy='omit')
            results.append({
                'Population': pop,
                'T-statistic': t_stat,
                'P-value': p_value,
                'Significant (p<0.05)': p_value < 0.05
            })

    stats_df = pd.DataFrame(results)
    return full_freq_df, stats_df

def create_boxplot(df):
    """Generates an interactive boxplot comparing responders and non-responders."""
    fig = px.box(
        df, 
        x='population', 
        y='percentage', 
        color='response',
        title='Cell Population Frequencies: Responders vs. Non-Responders',
        labels={
            'percentage': 'Relative Frequency (%)',
            'population': 'Cell Population',
            'response': 'Response to Miraclib'
        },
        color_discrete_map={'yes': 'blue', 'no': 'red'}
    )
    fig.update_layout(xaxis_title="Immune Cell Population", yaxis_title="Relative Frequency (%)")
    return fig

def get_subset_stats(df):
    """
    Filters for baseline melanoma samples on miraclib and computes summary stats.
    """
    subset_df = df[
        (df['condition'] == 'melanoma') &
        (df['treatment'] == 'miraclib') &
        (df['sample_type'] == 'PBMC') &
        (df['time_from_treatment_start'] == 0)
    ].copy()
    
    # To count subjects correctly, drop duplicate subject IDs
    unique_subjects_df = subset_df.drop_duplicates(subset=['subject_id'])
    
    project_counts = subset_df['project'].value_counts()
    responder_counts = unique_subjects_df['response'].value_counts()
    gender_counts = unique_subjects_df['sex'].value_counts()
    
    return {
        "project_counts": project_counts,
        "responder_counts": responder_counts,
        "gender_counts": gender_counts
    }