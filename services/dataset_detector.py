import pandas as pd
from typing import List, Dict, Any, Tuple
import streamlit as st

DOMAIN_KEYWORDS = {
    "Sales": ["sales", "revenue", "profit", "customer", "order", "product", "quantity", "discount", "region", "invoice", "price"],
    "HR": ["employee", "salary", "department", "attrition", "manager", "joining", "designation", "experience", "hr", "payroll", "turnover"],
    "Finance": ["expense", "income", "budget", "profit", "loss", "cashflow", "tax", "investment", "finance", "asset", "liability"],
    "Marketing": ["campaign", "clicks", "impressions", "ctr", "leads", "conversion", "channel", "ad", "marketing", "spend", "cost"],
    "Inventory": ["stock", "warehouse", "inventory", "supplier", "reorder", "sku", "quantity", "logistics", "supply"],
    "Customer Support": ["ticket", "resolution", "agent", "complaint", "response", "priority", "support", "satisfaction", "issue"],
    "Healthcare": ["patient", "doctor", "diagnosis", "treatment", "hospital", "clinic", "medical", "blood", "ward", "disease"],
    "Education": ["student", "teacher", "grade", "score", "attendance", "course", "school", "university", "exam", "assignment"],
    "E-Commerce": ["cart", "checkout", "shipping", "ecommerce", "seller", "basket", "transaction", "payment"]
}

def analyze_columns(df: pd.DataFrame) -> List[str]:
    return [str(col).lower() for col in df.columns]

def calculate_domain_scores(columns: List[str]) -> Dict[str, float]:
    scores = {}
    total_cols = len(columns)
    if total_cols == 0:
        return scores
        
    for domain, keywords in DOMAIN_KEYWORDS.items():
        match_count = sum(1 for col in columns for kw in keywords if kw in col)
        # We consider a 100% confidence if at least 3-4 distinct column matches are found in typical domains, 
        # or proportional to the number of columns.
        base_score = min((match_count / max(3, min(total_cols, 10))) * 100, 100.0)
        scores[domain] = base_score
        
    return scores

def detect_dataset_type(df: pd.DataFrame) -> Tuple[str, float, Dict[str, float]]:
    columns = analyze_columns(df)
    scores = calculate_domain_scores(columns)
    
    if not scores:
        return "General", 0.0, {}
        
    best_domain = max(scores, key=scores.get)
    best_score = scores[best_domain]
    
    if best_score < 20.0:
        return "General Dataset", best_score, scores
        
    return best_domain, best_score, scores

def generate_dataset_description(domain: str) -> str:
    descriptions = {
        "Sales": "This dataset appears to contain sales transactions including customers, products, revenue, and regional performance metrics.",
        "HR": "This dataset appears to contain human resources data including employee details, departmental structures, salaries, and attrition indicators.",
        "Finance": "This dataset appears to contain financial records covering income, expenses, budgets, and overall financial health metrics.",
        "Marketing": "This dataset appears to contain marketing data tracking campaigns, click-through rates, leads, and conversion metrics.",
        "Inventory": "This dataset appears to contain inventory logs including SKU details, warehouse stock levels, and supplier orders.",
        "Customer Support": "This dataset appears to contain customer service logs detailing support tickets, resolution times, and agent performance.",
        "Healthcare": "This dataset appears to contain medical or healthcare records including patient visits, treatments, and clinical metrics.",
        "Education": "This dataset appears to contain educational records tracking student performance, course enrollment, and institutional metrics.",
        "E-Commerce": "This dataset appears to contain e-commerce transactions focusing on online shopping behavior, cart checkouts, and shipping.",
        "General Dataset": "This is a general-purpose dataset containing miscellaneous records. We could not firmly classify it into a specific business domain."
    }
    return descriptions.get(domain, descriptions["General Dataset"])

def extract_business_entities(df: pd.DataFrame, domain: str) -> List[str]:
    # Extract columns that are typically identifiers or categories
    columns_lower = [str(col).lower() for col in df.columns]
    entities = []
    
    if domain in DOMAIN_KEYWORDS:
        keywords = DOMAIN_KEYWORDS[domain]
        for col in df.columns:
            if any(kw in str(col).lower() for kw in keywords):
                entities.append(col)
                
    # If not enough entities found via keywords, grab some high cardinality categories or numerics
    if len(entities) < 3:
        cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        num_cols = df.select_dtypes(include=['number']).columns.tolist()
        entities.extend(cat_cols[:2])
        entities.extend(num_cols[:2])
        
    return list(dict.fromkeys(entities)) # remove duplicates

def generate_kpi_suggestions(domain: str) -> List[str]:
    kpis = {
        "Sales": ["Total Revenue", "Total Orders", "Average Order Value", "Top Product", "Top Customer", "Revenue Growth"],
        "HR": ["Employee Count", "Average Salary", "Attrition Rate", "Department Distribution", "Tenure Analysis"],
        "Finance": ["Total Income", "Total Expenses", "Net Profit", "Profit Margin", "Budget Variance"],
        "Marketing": ["Total Campaigns", "Average CTR", "Total Conversions", "Cost Per Lead", "ROI"],
        "Inventory": ["Total Items in Stock", "Low Stock Alerts", "Warehouse Capacity", "Inventory Value"],
        "Customer Support": ["Total Tickets", "Average Resolution Time", "CSAT Score", "Tickets by Priority"],
        "Healthcare": ["Total Patients", "Average Length of Stay", "Readmission Rate", "Beds Available"],
        "Education": ["Total Students", "Average Grade", "Attendance Rate", "Graduation Rate"],
        "E-Commerce": ["Cart Abandonment Rate", "Total Transactions", "Average Shipping Time", "Customer Lifetime Value"],
        "General Dataset": ["Row Count", "Column Count", "Missing Value Ratio", "Duplicate Ratio"]
    }
    return kpis.get(domain, kpis["General Dataset"])

def generate_chart_suggestions(domain: str) -> List[str]:
    charts = {
        "Sales": ["Revenue by Region", "Revenue Trend", "Top Products", "Customer Distribution"],
        "HR": ["Department Distribution", "Salary Distribution", "Attrition by Department", "Headcount Trend"],
        "Finance": ["Income vs Expense", "Profit Margin Trend", "Cashflow Analysis", "Expense Breakdown"],
        "Marketing": ["Campaign Performance", "Conversion Funnel", "Lead Sources", "Click Trend"],
        "Inventory": ["Stock Levels by Category", "Reorder Alerts", "Warehouse Distribution"],
        "Customer Support": ["Tickets by Status", "Resolution Time Trend", "Agent Performance"],
        "Healthcare": ["Patient Demographics", "Admissions Trend", "Treatment Outcomes"],
        "Education": ["Grade Distribution", "Attendance Trends", "Course Enrollment"],
        "E-Commerce": ["Sales Funnel", "Revenue by Product Category", "Shipping Times"],
        "General Dataset": ["Distribution of Numeric Columns", "Categorical Value Counts", "Correlation Heatmap"]
    }
    return charts.get(domain, charts["General Dataset"])

def save_detection_results(dataset_type: str, confidence: float, entities: List[str], description: str, kpis: List[str], charts: List[str]):
    st.session_state["dataset_type"] = dataset_type
    st.session_state["dataset_confidence"] = confidence
    st.session_state["dataset_entities"] = entities
    st.session_state["dataset_description"] = description
    st.session_state["recommended_kpis"] = kpis
    st.session_state["recommended_charts"] = charts
