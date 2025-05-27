"""
Performance monitoring and loading indicators for the Data Insights application.

This module provides timing diagnostics, progress bars, and loading indicators
to track and optimize application performance.
"""

import streamlit as st
import time
import logging
from typing import Optional, Dict, Any
from contextlib import contextmanager
import pandas as pd

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """Track and display performance metrics for dashboard operations."""
    
    def __init__(self):
        self.timings = {}
        self.operation_count = 0
    
    @contextmanager
    def track_operation(self, operation_name: str, show_progress: bool = True, 
                       show_timing: bool = True, progress_text: Optional[str] = None):
        """
        Context manager to track operation timing and display progress.
        
        Args:
            operation_name: Name of the operation being tracked
            show_progress: Whether to show a progress bar/spinner
            show_timing: Whether to display timing information
            progress_text: Custom text to display in progress indicator
        """
        self.operation_count += 1
        start_time = time.time()
        
        # Display progress indicator
        progress_container = None
        spinner_container = None
        
        if show_progress:
            if progress_text:
                progress_container = st.empty()
                progress_container.info(f"⏳ {progress_text}")
            else:
                spinner_container = st.spinner(f"Loading {operation_name}...")
        
        try:
            yield
        finally:
            end_time = time.time()
            duration = end_time - start_time
            
            # Store timing data
            self.timings[operation_name] = duration
            
            # Clear progress indicators
            if progress_container:
                progress_container.empty()
            
            # Log timing information
            logger.info(f"Operation '{operation_name}' completed in {duration:.2f} seconds")
            
            # Display timing information if requested
            if show_timing and duration > 1.0:  # Only show for operations > 1 second
                st.success(f"✅ {operation_name} completed in {duration:.2f}s")
            elif show_timing and duration > 0.5:  # Warning for operations > 0.5 seconds
                st.warning(f"⚠️ {operation_name} took {duration:.2f}s")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of all tracked operations."""
        if not self.timings:
            return {"total_operations": 0, "total_time": 0, "operations": {}}
        
        total_time = sum(self.timings.values())
        slowest_operation = max(self.timings.items(), key=lambda x: x[1])
        
        return {
            "total_operations": len(self.timings),
            "total_time": total_time,
            "average_time": total_time / len(self.timings),
            "slowest_operation": slowest_operation,
            "operations": dict(sorted(self.timings.items(), key=lambda x: x[1], reverse=True))
        }
    
    def display_performance_summary(self):
        """Display a detailed performance summary in the sidebar."""
        summary = self.get_performance_summary()
        
        if summary["total_operations"] == 0:
            st.sidebar.info("No performance data available")
            return
        
        with st.sidebar.expander("🔍 Performance Diagnostics"):
            st.write(f"**Total Operations:** {summary['total_operations']}")
            st.write(f"**Total Time:** {summary['total_time']:.2f}s")
            st.write(f"**Average Time:** {summary['average_time']:.2f}s")
            
            if summary["slowest_operation"]:
                op_name, op_time = summary["slowest_operation"]
                st.write(f"**Slowest Operation:** {op_name} ({op_time:.2f}s)")
            
            st.write("**All Operations:**")
            for op_name, op_time in summary["operations"].items():
                color = "🔴" if op_time > 5.0 else "🟡" if op_time > 2.0 else "🟢"
                st.write(f"{color} {op_name}: {op_time:.2f}s")

@contextmanager
def loading_indicator(message: str, progress_bar: bool = False):
    """
    Simple loading indicator with optional progress bar.
    
    Args:
        message: Message to display while loading
        progress_bar: Whether to show an animated progress bar
    """
    container = st.empty()
    
    if progress_bar:
        # Animated progress bar
        progress = container.progress(0)
        status_text = st.empty()
        
        # Simulate progress animation
        for i in range(0, 101, 10):
            progress.progress(i)
            status_text.text(f"{message} ({i}%)")
            time.sleep(0.1)
        
        try:
            yield
        finally:
            progress.empty()
            status_text.empty()
    else:
        # Simple spinner
        with container:
            with st.spinner(message):
                yield

def track_data_loading(func):
    """Decorator to track data loading performance."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        # Extract meaningful names from function and arguments
        func_name = func.__name__
        if args and hasattr(args[0], '__class__'):
            func_name = f"{args[0].__class__.__name__}.{func_name}"
        
        logger.info(f"Starting data loading: {func_name}")
        
        try:
            result = func(*args, **kwargs)
            
            # Calculate timing
            duration = time.time() - start_time
            
            # Log results
            if isinstance(result, pd.DataFrame):
                logger.info(f"Data loading completed: {func_name} - {len(result):,} rows in {duration:.2f}s")
            else:
                logger.info(f"Data loading completed: {func_name} in {duration:.2f}s")
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Data loading failed: {func_name} after {duration:.2f}s - {str(e)}")
            raise
    
    return wrapper

def display_loading_diagnostics():
    """Display current loading status and performance tips."""
    with st.sidebar.expander("⚡ Performance Tips"):
        st.write("""
        **To improve loading times:**
        
        🎯 **Filter Data:** Use more specific date ranges and agency filters
        
        🔄 **Cache Usage:** Repeated queries use cached data (5min TTL)
        
        📊 **Tab Loading:** Tabs load data only when selected
        
        🛠️ **SQL Optimization:** Queries use optimized database functions
        
        📈 **Progressive Loading:** Large datasets load incrementally
        """)

def show_data_info(df: pd.DataFrame, operation_name: str = "Dataset"):
    """Display information about loaded data."""
    if df.empty:
        st.warning(f"⚠️ {operation_name} is empty")
    else:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📊 Rows", f"{len(df):,}")
        with col2:
            st.metric("📋 Columns", len(df.columns))
        with col3:
            memory_usage = df.memory_usage(deep=True).sum() / 1024 / 1024  # MB
            st.metric("💾 Memory", f"{memory_usage:.1f} MB")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()
