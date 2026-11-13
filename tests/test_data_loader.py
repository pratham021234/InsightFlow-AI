import pytest
import io
import pandas as pd
from services.data_loader import load_csv, load_excel, load_dataset, _sanitize_columns

def test_sanitize_columns():
    df = pd.DataFrame({" name ": [1], "name": [2], "": [3]})
    clean_df = _sanitize_columns(df)
    assert clean_df.columns[0] == "name"
    assert clean_df.columns[1] == "name_1"
    assert clean_df.columns[2] == "Unnamed"

def test_load_csv_valid():
    csv_data = b"Product,Revenue,Units\nWidget A,100.5,5\nWidget B,200.0,10\n"
    file = io.BytesIO(csv_data)
    df, meta, logs = load_csv(file, "test.csv")
    assert len(df) == 2
    assert meta["rows"] == 2
    assert meta["columns"] == 3
    assert "Widget A" in df["Product"].values
    assert any("Successfully" in log for log in logs)

def test_load_csv_empty():
    file = io.BytesIO(b"")
    with pytest.raises(ValueError, match="empty"):
        load_csv(file, "empty.csv")

def test_load_csv_no_records():
    file = io.BytesIO(b"Col1,Col2\n")
    with pytest.raises(ValueError, match="no records"):
        load_csv(file, "header_only.csv")

def test_load_csv_semicolon_delimiter():
    csv_data = b"Name;Score;Grade\nAlice;95;A\nBob;88;B\n"
    file = io.BytesIO(csv_data)
    df, meta, logs = load_csv(file, "test_semi.csv")
    assert len(df) == 2
    assert "Score" in df.columns
    assert df["Score"].iloc[0] == 95

def test_load_excel_valid():
    df_sample = pd.DataFrame({"ID": [1, 2], "Item": ["Alpha", "Beta"]})
    buf = io.BytesIO()
    df_sample.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    
    df, meta, logs = load_excel(buf, "test.xlsx")
    assert len(df) == 2
    assert meta["file_type"] == "excel"
    assert "Item" in df.columns

def test_load_dataset_unsupported():
    file = io.BytesIO(b"some data")
    with pytest.raises(ValueError, match="Unsupported file format"):
        load_dataset(file, "document.pdf")

