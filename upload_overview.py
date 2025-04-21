
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from utils.file_loader import load_file
from utils.variable_detection import detect_column_types

def safe_key(col):
    return col.replace(" ", "_").replace(".", "_")

def show_bar_chart(data, title, ylabel="% of Responses"):
    fig, ax = plt.subplots()
    data.plot(kind="bar", ax=ax)
    for i, val in enumerate(data):
        ax.text(i, val, f"{val:.1f}%", ha='center', va='bottom')
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    st.pyplot(fig)

def show():
    st.header("📥 Upload & Overview")

    uploaded_file = st.file_uploader("Upload your CSV or Excel file", type=["csv", "xls", "xlsx"])
    if uploaded_file:
        df = load_file(uploaded_file)
        if df is not None:
            st.session_state["df"] = df
            st.session_state["column_types"] = detect_column_types(df)

    if "df" in st.session_state:
        df = st.session_state["df"]
        column_types = st.session_state.get("column_types", detect_column_types(df))

        st.subheader("📄 Data Preview")
        st.dataframe(df.head())

        st.subheader("⚙️ Auto-Detected + Editable Variable Types")
        edited_types = {}
        for col in df.columns:
            default_type = column_types.get(col, "numeric")
            edited_types[col] = st.selectbox(
                f"{col}",
                ["numeric", "likert", "categorical", "checkbox", "matrix", "open_ended"],
                index=["numeric", "likert", "categorical", "checkbox", "matrix", "open_ended"].index(default_type),
                key=f"type_{safe_key(col)}"
            )
        st.session_state["column_types"] = edited_types

        st.subheader("📊 Segment and Visualize Data")
        segment_col = st.selectbox("Segment all charts by", ["(none)"] + [col for col, typ in edited_types.items() if typ == "categorical"])
        numeric_or_likert = [col for col, typ in edited_types.items() if typ in ["numeric", "likert"]]

        for col in numeric_or_likert:
            if segment_col == "(none)":
                pct = df[col].value_counts(normalize=True).sort_index() * 100
                show_bar_chart(pct, f"{col} (%)")
            else:
                grouped = df.groupby(segment_col)[col].value_counts(normalize=True).unstack().fillna(0) * 100
                for val in grouped.index:
                    pct = grouped.loc[val]
                    show_bar_chart(pct, f"{col} — {segment_col}: {val}")

        # Initialize group states
        st.session_state.setdefault("checkbox_map", {})
        st.session_state.setdefault("matrix_map", {})
        st.session_state.setdefault("show_checkbox_form", False)
        st.session_state.setdefault("show_matrix_form", False)

        st.subheader("🧩 Group Checkbox & Matrix Questions")

        # Checkbox groups display
        st.markdown("### ✅ Existing Checkbox Groups")
        for group_name, columns in st.session_state["checkbox_map"].items():
            with st.expander(f"{group_name}"):
                st.markdown(f"**Columns:** {', '.join(columns)}")
                if st.button(f"❌ Delete Checkbox Group: {group_name}"):
                    del st.session_state["checkbox_map"][group_name]
                    st.experimental_rerun()

        if st.button("➕ Create New Checkbox Group"):
            st.session_state["show_checkbox_form"] = not st.session_state["show_checkbox_form"]

        if st.session_state["show_checkbox_form"]:
            name = st.text_input("Checkbox Group Name")
            checkbox_cols = [col for col, typ in edited_types.items() if typ == "checkbox"]
            selected_cols = st.multiselect("Select Checkbox Columns", checkbox_cols)
            if st.button("✅ Save Checkbox Group"):
                if name and selected_cols:
                    st.session_state["checkbox_map"][name] = selected_cols
                    st.success(f"Checkbox group '{name}' created.")
                    st.experimental_rerun()

        # Matrix groups display
        st.markdown("### ✅ Existing Matrix Groups")
        for group_name, columns in st.session_state["matrix_map"].items():
            with st.expander(f"{group_name}"):
                st.markdown(f"**Columns:** {', '.join(columns)}")
                if st.button(f"❌ Delete Matrix Group: {group_name}"):
                    del st.session_state["matrix_map"][group_name]
                    st.experimental_rerun()

        if st.button("➕ Create New Matrix Group"):
            st.session_state["show_matrix_form"] = not st.session_state["show_matrix_form"]

        if st.session_state["show_matrix_form"]:
            name = st.text_input("Matrix Group Name")
            matrix_cols = [col for col, typ in edited_types.items() if typ == "matrix"]
            selected_cols = st.multiselect("Select Matrix Columns", matrix_cols)
            if st.button("✅ Save Matrix Group"):
                if name and selected_cols:
                    st.session_state["matrix_map"][name] = selected_cols
                    st.success(f"Matrix group '{name}' created.")
                    st.experimental_rerun()

        # Charts
        st.markdown("✅ Checkbox Group Charts")
        for group, cols in st.session_state["checkbox_map"].items():
            if segment_col == "(none)":
                counts = (df[cols].notnull()).sum() / len(df) * 100
                show_bar_chart(counts, f"{group} - % Selected")
            else:
                for val in df[segment_col].dropna().unique():
                    segment_df = df[df[segment_col] == val]
                    counts = (segment_df[cols].notnull()).sum() / len(segment_df) * 100
                    show_bar_chart(counts, f"{group} - % Selected ({segment_col}: {val})")

        st.markdown("✅ Matrix Group Charts")
        for group, cols in st.session_state["matrix_map"].items():
            if segment_col == "(none)":
                means = df[cols].mean()
                show_bar_chart(means, f"{group} - Avg Scores", ylabel="Avg Score")
            else:
                for val in df[segment_col].dropna().unique():
                    segment_df = df[df[segment_col] == val]
                    means = segment_df[cols].mean()
                    show_bar_chart(means, f"{group} - Avg Scores ({segment_col}: {val})", ylabel="Avg Score")
