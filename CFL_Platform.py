import pandas as pd
import streamlit as st
import ast  # To safely convert list-like strings

# Function to safely parse list-like strings
def safe_list_conversion(value):
    try:
        if pd.isna(value) or value.strip() == "":
            return []  # Return empty list if value is NaN or empty
        return ast.literal_eval(value) if isinstance(value, str) else value
    except (ValueError, SyntaxError):
        return []  # Return empty list in case of parsing errors

# Function to format keywords (replace underscores with spaces)
def format_keyword(keyword):
    return keyword.replace("_", " ") if isinstance(keyword, str) else keyword

# Function to load data
@st.cache_data
def load_data(filepath):
    try:
        df_all = pd.read_csv(filepath)

        # Define expected columns
        expected_columns = [
            "DOI", "Category", "Subcategory", "Keywords",
            "top_5_similar", "top_10_similar", "top_15_similar",
            "Paper Title", "Author", "Journal", "Year", "Sample size (Firms)", 
            "Sample size (Observations)", "Sample firms", "Begin sample", "End sample",
            "Data Source for Narrative", "Data Source for Narrative (Other)",
            "Linguistic Variable(s) - Category", "Linguistic Variable(s) - Category (Details)",
            "Linguistic Variable(s) - Other", "Linguistic Variable(s) - Use of Thesaurus",
            "Linguistic Variable(s) - Thesaurus Development Details",
            "Outcome variable(s) category", "Outcome variable(s) - Other", "Reference"
        ]

        # Keep only available columns
        df = df_all[[col for col in expected_columns if col in df_all.columns]].copy()

        # Strip column names
        df.columns = [col.strip() for col in df.columns]

        # Convert "Keywords" column to a list
        if "Keywords" in df.columns:
            df["Keywords"] = df["Keywords"].apply(lambda x: list(set(x.split())) if isinstance(x, str) else [])

        # Convert AI-generated keyword columns and remove duplicates
        for col in ["top_5_similar", "top_10_similar", "top_15_similar"]:
            if col in df.columns:
                df[col] = df[col].apply(safe_list_conversion).apply(set)  # Remove duplicates

        return df
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return None

# Define dataset path
DATA_PATH = "https://raw.githubusercontent.com/arioncheong/finance-lexicon/refs/heads/main/Analysis1_merge_part.csv"
df = load_data(DATA_PATH)

# Initialize session state
if "selected_metadata" not in st.session_state:
    st.session_state.selected_metadata = {}

if "clicked_keyword" not in st.session_state:
    st.session_state.clicked_keyword = None

# Sidebar Navigation (Always Visible)
st.sidebar.header("📌 Navigation")

# Main App Title
st.title("📊 Comprehensive Financial Lexicon (CFL) Explorer")
st.markdown("Explore financial terms categorized under CFL.")

# **📂 Browse Categories**
st.subheader("📂 Explore Categories")

if df is not None:
    # Select category
    selected_category = st.selectbox("Select a Category:", [""] + sorted(df["Category"].dropna().unique()))

    if selected_category:
        # Select subcategory
        filtered_subcategories = df[df["Category"] == selected_category]["Subcategory"].dropna().unique()
        selected_subcategory = st.selectbox("Select a Subcategory:", [""] + sorted(filtered_subcategories))

        if selected_subcategory:
            filtered_data = df[(df["Category"] == selected_category) & (df["Subcategory"] == selected_subcategory)]

            # Collect original keywords and AI-generated keywords
            original_keywords = set()
            ai_keywords = set()

            for _, row in filtered_data.iterrows():
                if "Keywords" in row and isinstance(row["Keywords"], list):
                    original_keywords.update(row["Keywords"])
                
                for col in ["top_5_similar", "top_10_similar", "top_15_similar"]:
                    if col in row and isinstance(row[col], set):  # Using set to ensure uniqueness
                        ai_keywords.update(row[col])

            # Convert keywords to formatted text for download
            original_keywords_formatted = "\n".join(sorted(format_keyword(kw) for kw in original_keywords))
            all_keywords_formatted = "\n".join(sorted(format_keyword(kw) for kw in original_keywords.union(ai_keywords)))

            # Convert to CSV format
            original_csv = original_keywords_formatted.encode("utf-8")
            all_csv = all_keywords_formatted.encode("utf-8")

            # **Download buttons placed here next to subcategory selection**
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("📥 Download Filtered Data", original_csv, "filtered_keywords.csv", "text/csv", key="filtered_data_download")
            with col2:
                st.download_button("📥 Download Filtered + AI-Generated Data", all_csv, "all_keywords.csv", "text/csv", key="ai_data_download")

            # **Display Keywords**
            for keyword in sorted(original_keywords):  # Sorting for consistency
                formatted_keyword = format_keyword(keyword)  # Format keyword before displaying

                if st.button(formatted_keyword, key=f"{selected_category}_{selected_subcategory}_{keyword}"):
                    st.session_state.clicked_keyword = keyword
                    st.session_state.selected_metadata[keyword] = filtered_data.iloc[0].to_dict()  # Use first entry

else:
    st.warning("No data available. Please check the file path.")

# **Sidebar: Always Show Metadata**
with st.sidebar:
    st.subheader("✅ Selected Keyword Details")

    if st.session_state.clicked_keyword:
        keyword = st.session_state.clicked_keyword
        metadata = st.session_state.selected_metadata.get(keyword, {})

        # **Show AI-Generated Keywords Above Metadata**
        ai_keywords = set()
        for col in ["top_5_similar", "top_10_similar", "top_15_similar"]:
            if col in metadata and isinstance(metadata[col], set):
                ai_keywords.update(metadata[col])

        if ai_keywords:
            st.write("### 🤖 AI-Generated Keywords:")
            st.write(", ".join(sorted(format_keyword(kw) for kw in ai_keywords)))

        # **Metadata is always visible**
        st.write(f"**📄 Paper Title:** {metadata.get('Paper Title', 'N/A')}")
        st.write(f"**👨‍🏫 Author:** {metadata.get('Author', 'N/A')}")
        st.write(f"**📕 Journal:** {metadata.get('Journal', 'N/A')}")
        st.write(f"**📅 Year:** {metadata.get('Year', 'N/A')}")
        st.write(f"**📊 Sample Size (Firms):** {metadata.get('Sample size (Firms)', 'N/A')}")
        st.write(f"**📉 Sample Size (Observations):** {metadata.get('Sample size (Observations)', 'N/A')}")
        st.write(f"**🏢 Sample Firms:** {metadata.get('Sample firms', 'N/A')}")
        st.write(f"**📌 Data Source for Narrative:** {metadata.get('Data Source for Narrative', 'N/A')}")
        st.write(f"**📚 Linguistic Variable - Category:** {metadata.get('Linguistic Variable(s) - Category', 'N/A')}")
        st.write(f"**📙 Linguistic Variable - Use of Thesaurus:** {metadata.get('Linguistic Variable(s) - Use of Thesaurus', 'N/A')}")
        st.write(f"**📖 Linguistic Variable - Thesaurus Development Details:** {metadata.get('Linguistic Variable(s) - Thesaurus Development Details', 'N/A')}")
        st.write(f"**🔗 Reference:** {metadata.get('Reference', 'N/A')}")
