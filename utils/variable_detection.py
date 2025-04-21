
def detect_column_types(df):
    column_types = {}
    for col in df.columns:
        if df[col].dtype == 'object':
            if df[col].nunique() <= 10:
                column_types[col] = 'categorical'
            elif df[col].str.len().mean() > 20:
                column_types[col] = 'open_ended'
            else:
                column_types[col] = 'text'
        elif df[col].dropna().between(1, 7).all():
            column_types[col] = 'likert'
        else:
            column_types[col] = 'numeric'
    return column_types
