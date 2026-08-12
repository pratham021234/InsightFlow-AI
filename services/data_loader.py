import pandas as pd
from typing import Tuple, Dict, Any, List

def _format_size(size_bytes: int) -> str:
    """Format bytes into KB or MB."""
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

def _extract_metadata(df: pd.DataFrame, file_size: int, filename: str, encoding: str, file_type: str) -> Dict[str, Any]:
    """Generate extensive metadata for the uploaded dataset."""
    memory_usage = df.memory_usage(deep=True).sum()
    return {
        "filename": filename,
        "rows": len(df),
        "columns": len(df.columns),
        "memory_usage": _format_size(memory_usage),
        "file_size": _format_size(file_size),
        "encoding": encoding,
        "file_type": file_type
    }

def load_csv(file, filename: str) -> Tuple[pd.DataFrame, Dict[str, Any], List[str]]:
    """Load a CSV file using encoding fallback loops and auto-delimiter detection."""
    encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252", "ISO-8859-1"]
    logs = []
    
    file.seek(0)
    content = file.read()
    if not content:
        raise ValueError("The uploaded file is empty.")
    
    file_size = len(content)
    df = None
    success_enc = None
    
    for enc in encodings:
        logs.append(f"Attempting {enc.upper()} encoding...")
        try:
            file.seek(0)
            # engine='python' and sep=None allow auto delimiter detection
            df = pd.read_csv(file, encoding=enc, sep=None, engine='python')
            logs.append(f"Successfully loaded using {enc.upper()}")
            success_enc = enc
            break
        except UnicodeDecodeError:
            logs.append(f"Failed decoding with {enc.upper()}")
        except pd.errors.EmptyDataError:
            raise ValueError("The uploaded dataset contains no records.")
        except Exception as e:
            logs.append(f"Failed parsing with {enc.upper()}: {str(e)}")
            
    if df is None:
        raise ValueError("Unable to read file. The file may be corrupted or use an unsupported encoding format.")
        
    if df.empty or len(df) == 0:
        raise ValueError("The uploaded dataset contains no records.")
        
    if len(df.columns) == 0:
        raise ValueError("The uploaded dataset contains no columns.")
        
    metadata = _extract_metadata(df, file_size, filename, success_enc, "csv")
    return df, metadata, logs

def load_excel(file, filename: str) -> Tuple[pd.DataFrame, Dict[str, Any], List[str]]:
    """Load an Excel file robustly."""
    logs = []
    try:
        file.seek(0)
        content = file.read()
        if not content:
            raise ValueError("The uploaded file is empty.")
            
        file.seek(0)
        file_size = len(content)
        logs.append("Attempting to parse Excel workbook...")
        
        df = pd.read_excel(file)
        logs.append("Successfully loaded Excel data.")
        
        if df.empty or len(df) == 0:
            raise ValueError("The uploaded dataset contains no records.")
            
        if len(df.columns) == 0:
            raise ValueError("The uploaded dataset contains no columns.")
            
        metadata = _extract_metadata(df, file_size, filename, "N/A (Binary)", "excel")
        return df, metadata, logs
        
    except ValueError as ve:
        raise ve
    except Exception as e:
        raise ValueError("Unable to read file. The file may be corrupted.")

def load_dataset(file, filename: str) -> Tuple[pd.DataFrame, Dict[str, Any], List[str]]:
    """Automatically detect file type and load the dataset."""
    if filename.lower().endswith(".csv"):
        return load_csv(file, filename)
    elif filename.lower().endswith((".xlsx", ".xls")):
        return load_excel(file, filename)
    else:
        raise ValueError("Unsupported file format.")
