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

if "selected_category" not in st.session_state:
    st.session_state.selected_category = None

if "selected_subcategory" not in st.session_state:
    st.session_state.selected_subcategory = None

# **📌 Sidebar: Always Visible**
st.sidebar.header("📌 Navigation")

# **Main Layout: Sidebar + Main Content**
st.title("📊 Comprehensive Financial Lexicon (CFL) Explorer")
st.markdown("Explore financial terms categorized under CFL.")

# **📂 Browse Categories**
st.subheader("📂 Explore Categories")

if df is not None:
    # Select category
    selected_category = st.selectbox("Select a Category:", [""] + sorted(df["Category"].dropna().unique()))

    # Reset subcategory selection if category changes
    if selected_category != st.session_state.selected_category:
        st.session_state.selected_category = selected_category
        st.session_state.selected_subcategory = None  # Reset subcategory
        st.session_state.clicked_keyword = None
        st.session_state.selected_metadata = {}

    if selected_category:
        # Select subcategory
        filtered_subcategories = df[df["Category"] == selected_category]["Subcategory"].dropna().unique()
        selected_subcategory = st.selectbox("Select a Subcategory:", [""] + sorted(filtered_subcategories))

        # Reset keywords if subcategory changes
        if selected_subcategory != st.session_state.selected_subcategory:
            st.session_state.selected_subcategory = selected_subcategory
            st.session_state.clicked_keyword = None
            st.session_state.selected_metadata = {}

        if selected_subcategory:
            filtered_data = df[(df["Category"] == selected_category) & (df["Subcategory"] == selected_subcategory)]

            # Collect original keywords and AI-generated keywords
            original_keywords = set()
            ai_keywords = set()
            keyword_metadata = {}  # Store metadata for each keyword

            for _, row in filtered_data.iterrows():
                if "Keywords" in row and isinstance(row["Keywords"], list):
                    for kw in row["Keywords"]:
                        formatted_kw = format_keyword(kw)
                        original_keywords.add(formatted_kw)
                        keyword_metadata[formatted_kw] = row.to_dict()  # Ensure correct metadata linkage
                
                # Collect AI-generated keywords
                for col in ["top_5_similar", "top_10_similar", "top_15_similar"]:
                    if col in row and isinstance(row[col], set):
                        ai_keywords.update(row[col])

            # Convert to CSV format
            original_csv = "\n".join(sorted(original_keywords)).encode("utf-8")
            all_csv = "\n".join(sorted(original_keywords.union(ai_keywords))).encode("utf-8")

            # **Download Buttons**
            st.download_button("📥 Download Filtered Data", original_csv, "filtered_keywords.csv", "text/csv")
            st.download_button("📥 Download Filtered + AI-Generated Data", all_csv, "all_keywords.csv", "text/csv")

            # **Display Keywords**
            for keyword in sorted(original_keywords):
                if st.button(keyword, key=f"btn_{keyword}"):
                    st.session_state.clicked_keyword = keyword
                    st.session_state.selected_metadata = keyword_metadata[keyword]

# **📌 Sidebar: Always Visible**
with st.sidebar:
    st.subheader("✅ Selected Keyword Details")

    if st.session_state.clicked_keyword:
        keyword = st.session_state.clicked_keyword
        metadata = st.session_state.selected_metadata

        # **Show AI-Generated Keywords Above Metadata**
        ai_keywords = set()
        for col in ["top_5_similar", "top_10_similar", "top_15_similar"]:
            if col in metadata and isinstance(metadata[col], set):
                ai_keywords.update(metadata[col])

        if ai_keywords:
            st.write("### 🤖 AI-Generated Keywords:")
            st.write(", ".join(sorted(format_keyword(kw) for kw in ai_keywords)))

        # **Metadata is now updated on each click**
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
