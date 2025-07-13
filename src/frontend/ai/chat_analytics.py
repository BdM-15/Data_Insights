"""
Chat Analytics Dashboard

Provides insights into LLM behavior, tool usage, and conversation patterns.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import sys
import os

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../backend"))

try:
    from backend.ai.chat_logger import ChatLogger
    logger_available = True
except ImportError:
    logger_available = False
    st.error("Chat logging system not available")

def load_chat_analytics(days: int = 7):
    """Load chat analytics data."""
    if not logger_available:
        return None
    
    try:
        chat_logger = ChatLogger()
        return chat_logger.get_interaction_analytics(days)
    except Exception as e:
        st.error(f"Failed to load analytics: {e}")
        return None

def load_recent_chats(limit: int = 50):
    """Load recent chat interactions."""
    if not logger_available:
        return pd.DataFrame()
    
    try:
        chat_logger = ChatLogger()
        if not chat_logger.connection:
            return pd.DataFrame()
        
        query = """
        SELECT 
            id,
            user_query,
            llm_response,
            model_name,
            model_temperature,
            processing_time_ms,
            tools_used,
            status,
            user_feedback,
            created_at
        FROM app_logs.chat_logs 
        ORDER BY created_at DESC 
        LIMIT %s
        """
        
        df = pd.read_sql_query(query, chat_logger.connection, params=[limit])
        return df
        
    except Exception as e:
        st.error(f"Failed to load recent chats: {e}")
        return pd.DataFrame()

def load_tool_usage_stats():
    """Load tool usage statistics."""
    if not logger_available:
        return pd.DataFrame()
    
    try:
        chat_logger = ChatLogger()
        if not chat_logger.connection:
            return pd.DataFrame()
        
        query = """
        SELECT 
            jsonb_array_elements(tools_used)->>'name' as tool_name,
            COUNT(*) as usage_count,
            AVG((jsonb_array_elements(tools_used)->>'execution_time_ms')::int) as avg_execution_time
        FROM app_logs.chat_logs 
        WHERE tools_used IS NOT NULL 
          AND created_at >= NOW() - INTERVAL '30 days'
        GROUP BY tool_name
        ORDER BY usage_count DESC
        """
        
        df = pd.read_sql_query(query, chat_logger.connection)
        return df
        
    except Exception as e:
        st.error(f"Failed to load tool usage stats: {e}")
        return pd.DataFrame()

def main():
    """Main dashboard function."""
    st.set_page_config(page_title="Chat Analytics", page_icon="📊", layout="wide")
    
    st.title("🧠 LLM Chat Analytics Dashboard")
    st.markdown("Analyze LLM behavior, tool usage, and conversation patterns")
    
    if not logger_available:
        st.error("Chat logging system not available. Please check your database connection.")
        return
    
    # Sidebar controls
    st.sidebar.header("📋 Controls")
    days_filter = st.sidebar.selectbox("Time Range", [1, 7, 14, 30], index=1)
    chat_limit = st.sidebar.slider("Recent Chats Limit", 10, 200, 50)
    
    # Load analytics data
    analytics = load_chat_analytics(days_filter)
    recent_chats = load_recent_chats(chat_limit)
    tool_stats = load_tool_usage_stats()
    
    # Main metrics
    if analytics:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Interactions", int(analytics.get('total_interactions', 0)))
        
        with col2:
            avg_time = analytics.get('avg_processing_time', 0)
            st.metric("Avg Processing Time", f"{avg_time:.0f}ms" if avg_time else "N/A")
        
        with col3:
            error_count = analytics.get('error_count', 0)
            total = analytics.get('total_interactions', 1)
            error_rate = (error_count / total) * 100 if total > 0 else 0
            st.metric("Error Rate", f"{error_rate:.1f}%")
        
        with col4:
            avg_rating = analytics.get('avg_rating', 0)
            st.metric("Avg User Rating", f"{avg_rating:.1f}/5" if avg_rating else "N/A")
    
    # Tool Usage Chart
    if not tool_stats.empty:
        st.subheader("🔧 Tool Usage Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.bar(
                tool_stats, 
                x='tool_name', 
                y='usage_count',
                title="Tool Usage Frequency",
                color='usage_count',
                color_continuous_scale='Blues'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(
                tool_stats, 
                x='tool_name', 
                y='avg_execution_time',
                title="Average Tool Execution Time",
                color='avg_execution_time',
                color_continuous_scale='Reds'
            )
            fig.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
    
    # Processing Time Trend
    if not recent_chats.empty and 'processing_time_ms' in recent_chats.columns:
        st.subheader("⏱️ Processing Time Trends")
        
        # Convert datetime and create time series
        recent_chats['created_at'] = pd.to_datetime(recent_chats['created_at'])
        recent_chats['hour'] = recent_chats['created_at'].dt.floor('H')
        
        hourly_stats = recent_chats.groupby('hour').agg({
            'processing_time_ms': ['mean', 'count'],
            'status': lambda x: (x == 'error').sum()
        }).reset_index()
        
        hourly_stats.columns = ['hour', 'avg_time', 'interaction_count', 'error_count']
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=hourly_stats['hour'],
            y=hourly_stats['avg_time'],
            mode='lines+markers',
            name='Avg Processing Time (ms)',
            yaxis='y'
        ))
        
        fig.add_trace(go.Bar(
            x=hourly_stats['hour'],
            y=hourly_stats['interaction_count'],
            name='Interactions per Hour',
            yaxis='y2',
            opacity=0.7
        ))
        
        fig.update_layout(
            title="Processing Time vs Interaction Volume",
            xaxis_title="Time",
            yaxis=dict(title="Processing Time (ms)", side="left"),
            yaxis2=dict(title="Interactions", side="right", overlaying="y"),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Recent Conversations
    st.subheader("💬 Recent Conversations")
    
    if not recent_chats.empty:
        # Add expandable rows for conversation details
        for idx, row in recent_chats.head(10).iterrows():
            with st.expander(f"Chat {row['id']} - {row['created_at'].strftime('%Y-%m-%d %H:%M:%S')}"):
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.write("**User Query:**")
                    st.write(row['user_query'][:500] + "..." if len(row['user_query']) > 500 else row['user_query'])
                    
                    st.write("**Model:**", row['model_name'])
                    st.write("**Status:**", row['status'])
                    st.write("**Processing Time:**", f"{row['processing_time_ms']}ms" if pd.notna(row['processing_time_ms']) else "N/A")
                
                with col2:
                    st.write("**Response:**")
                    st.write(row['llm_response'][:500] + "..." if len(row['llm_response']) > 500 else row['llm_response'])
                    
                    if row['tools_used'] and pd.notna(row['tools_used']):
                        try:
                            tools = json.loads(row['tools_used']) if isinstance(row['tools_used'], str) else row['tools_used']
                            tool_names = [tool.get('name', 'Unknown') for tool in tools]
                            st.write("**Tools Used:**", ", ".join(tool_names))
                        except:
                            st.write("**Tools Used:** Error parsing")
                    
                    if row['user_feedback'] and pd.notna(row['user_feedback']):
                        st.write("**User Rating:**", f"{row['user_feedback']}/5")
    else:
        st.info("No recent conversations found.")
    
    # Raw data view
    with st.expander("📊 Raw Data"):
        if not recent_chats.empty:
            st.dataframe(recent_chats)
        else:
            st.info("No data available")

if __name__ == "__main__":
    main()
