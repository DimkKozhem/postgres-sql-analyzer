"""Модуль стилей и общих UI компонентов."""

import streamlit as st
import logging
from typing import Tuple
from app.utils import ui, validator

logger = logging.getLogger(__name__)


def apply_custom_styles() -> None:
    """Применяет кастомные стили к приложению."""
    st.markdown("""
    <style>
    /* Основные стили */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
        margin: 0.5rem 0;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .error-box {
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Темные стили для вкладок */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
        background-color: #2d3748;
        padding: 4px;
        border-radius: 8px 8px 0px 0px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #4a5568;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-left: 20px;
        padding-right: 20px;
        color: #ffffff;
        border: 1px solid #718096;
        margin-right: 2px;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #1a202c;
        border-bottom: 3px solid #1f77b4;
        color: #ffffff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #2d3748;
        color: #ffffff;
        transform: translateY(-1px);
    }
    
    .stTabs [data-baseweb="tab"]:focus {
        background-color: #1a202c;
        color: #ffffff;
        outline: 2px solid #1f77b4;
    }
    
    /* Стили для содержимого вкладок */
    .stTabs [data-baseweb="tab-panel"] {
        background-color: #1a202c;
        border-radius: 0px 8px 8px 8px;
        padding: 20px;
        margin-top: -1px;
        border: 1px solid #4a5568;
        border-top: none;
    }
    
    /* Темные стили для sidebar */
    .css-1d391kg {
        background-color: #2d3748;
    }
    
    .css-1d391kg .stSelectbox > div > div {
        background-color: #4a5568;
        color: #ffffff;
    }
    
    .css-1d391kg .stTextInput > div > div > input {
        background-color: #4a5568;
        color: #ffffff;
        border: 1px solid #718096;
    }
    
    .css-1d391kg .stNumberInput > div > div > input {
        background-color: #4a5568;
        color: #ffffff;
        border: 1px solid #718096;
    }
    
    .css-1d391kg .stSlider > div > div > div {
        background-color: #4a5568;
    }
    
    /* Стили для кнопок */
    .stButton > button {
        background-color: #1f77b4;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #1565c0;
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* Стили для кнопок подключения */
    .stButton > button[kind="primary"] {
        background-color: #38a169;
        color: white;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #2f855a;
    }
    
    .stButton > button[kind="secondary"] {
        background-color: #e53e3e;
        color: white;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background-color: #c53030;
    }
    
    /* Стили для отключенных кнопок */
    .stButton > button:disabled {
        background-color: #a0aec0;
        color: #718096;
        cursor: not-allowed;
        transform: none;
    }
    
    .stButton > button:disabled:hover {
        background-color: #a0aec0;
        transform: none;
        box-shadow: none;
    }
    
    /* Стили для метрик */
    .metric-container {
        background-color: #2d3748;
        border: 1px solid #4a5568;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .metric-value {
        color: #1f77b4;
        font-size: 2rem;
        font-weight: bold;
    }
    
    .metric-label {
        color: #a0aec0;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
    
    /* Стили для таблиц */
    .stDataFrame {
        background-color: #2d3748;
        border: 1px solid #4a5568;
        border-radius: 8px;
    }
    
    /* Стили для кода */
    .stCode {
        background-color: #1a202c;
        border: 1px solid #4a5568;
        border-radius: 6px;
    }
    
    /* Общие темные стили */
    .main .block-container {
        background-color: #1a202c;
        color: #ffffff;
    }
    
    .stMarkdown {
        color: #ffffff;
    }
    
    .stInfo {
        background-color: #2d3748;
        border: 1px solid #4a5568;
        color: #ffffff;
    }
    
    .stSuccess {
        background-color: #22543d;
        border: 1px solid #38a169;
        color: #ffffff;
    }
    
    .stWarning {
        background-color: #744210;
        border: 1px solid #d69e2e;
        color: #ffffff;
    }
    
    .stError {
        background-color: #742a2a;
        border: 1px solid #e53e3e;
        color: #ffffff;
    }
    
    /* Стили для информационных сообщений */
    .info-message {
        background-color: #2d3748;
        border: 1px solid #4a5568;
        border-radius: 8px;
        padding: 2rem;
        margin: 2rem 0;
        text-align: center;
        color: #ffffff;
    }
    
    .info-message h3 {
        color: #1f77b4;
        margin-bottom: 1rem;
        font-size: 1.5rem;
    }
    
    .info-message p {
        color: #e2e8f0;
        font-size: 1.1rem;
        margin: 0;
    }
    
    /* Стили для сообщений о подключении */
    .connection-message {
        background-color: #2d3748;
        border: 1px solid #4a5568;
        border-radius: 8px;
        padding: 2rem;
        margin: 2rem 0;
        text-align: center;
        color: #ffffff;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .connection-message h3 {
        color: #1f77b4;
        margin-bottom: 1rem;
        font-size: 1.5rem;
        font-weight: 600;
    }
    
    .connection-message p {
        color: #e2e8f0;
        font-size: 1.1rem;
        margin: 0;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)


def show_connection_status(dsn: str) -> Tuple[bool, str]:
    """Показывает статус подключения к базе данных."""
    try:
        # Тестируем подключение
        connection_success, connection_message = validator.validate_database_connection(dsn)
        
        if connection_success:
            st.success("✅ Подключение к БД активно")
            return True, "Подключено"
        else:
            st.error(f"❌ {connection_message}")
            return False, connection_message
            
    except Exception as e:
        error_message = f"Ошибка проверки подключения: {str(e)}"
        st.error(f"❌ {error_message}")
        logger.error(f"Ошибка в show_connection_status: {e}")
        return False, error_message


def create_metric_card(title: str, value: str, delta: str = None, help_text: str = None):
    """Создает карточку с метрикой."""
    with st.container():
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{value}</div>
            <div class="metric-label">{title}</div>
            {f'<div class="metric-delta">{delta}</div>' if delta else ''}
            {f'<div class="metric-help">{help_text}</div>' if help_text else ''}
        </div>
        """, unsafe_allow_html=True)


def show_warning(message: str):
    """Показывает предупреждение."""
    st.markdown(f"""
    <div class="warning-box">
        ⚠️ {message}
    </div>
    """, unsafe_allow_html=True)


def show_error(message: str):
    """Показывает ошибку."""
    st.markdown(f"""
    <div class="error-box">
        ❌ {message}
    </div>
    """, unsafe_allow_html=True)


def show_success(message: str):
    """Показывает успешное сообщение."""
    st.markdown(f"""
    <div class="success-box">
        ✅ {message}
    </div>
    """, unsafe_allow_html=True)
