"""
contract_schema_utils.py

Module for schema-aware contract logic to support agentic workflows.

This module provides foundational functions and classes for identifying, counting, and aggregating contract awards and obligations using schema logic. All contract-related logic should be placed here for maintainability and auditability.

Google-style docstrings and PEP8 formatting are enforced.
"""

from typing import List, Dict, Any, Optional
import re
import pandas as pd

class ContractSchemaUtils:
    """Utility class for schema-aware contract logic."""

    @staticmethod
    def is_base_award(row: Dict[str, Any]) -> bool:
        """
        Determine if a record is a base contract award (not a modification).

        Args:
            row: Dictionary representing a contract record.

        Returns:
            True if modification_number == '0', else False.
        """
        return str(row.get('modification_number', '')) == '0'

    @staticmethod
    def is_idv_or_idc(unique_key: str) -> bool:
        """
        Determine if a contract_award_unique_key represents an IDV/IDC vehicle/order.

        Args:
            unique_key: The contract_award_unique_key string.

        Returns:
            True if key starts with 'CONT_IDV_', else False.
        """
        return unique_key.startswith('CONT_IDV_')

    @staticmethod
    def is_award_or_mod(unique_key: str) -> bool:
        """
        Determine if a contract_award_unique_key represents an award or modification.

        Args:
            unique_key: The contract_award_unique_key string.

        Returns:
            True if key starts with 'CONT_AWD_', else False.
        """
        return unique_key.startswith('CONT_AWD_')

    @staticmethod
    def count_base_awards(df: pd.DataFrame) -> int:
        """
        Count the number of base contract awards in a DataFrame.

        Args:
            df: DataFrame containing contract records.

        Returns:
            Number of base awards (modification_number == '0').
        """
        return df[df['modification_number'] == '0'].shape[0]

    @staticmethod
    def sum_obligations(df: pd.DataFrame) -> float:
        """
        Sum all obligations (including deobligations) for contracts in a DataFrame.

        Args:
            df: DataFrame containing contract records.

        Returns:
            Total obligation value (sum of federal_action_obligation).
        """
        return df['federal_action_obligation'].sum()

    # Reason: This module centralizes all schema logic for contracts, enabling maintainable, testable, and auditable agent workflows.
