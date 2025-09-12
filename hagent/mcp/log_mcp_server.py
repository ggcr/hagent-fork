#!/usr/bin/env python3
"""
MCP Server Logging Utilities

This module provides logging functionality for MCP servers including
transaction logging and raw I/O logging capabilities.
"""

from __future__ import annotations

import datetime
import json
import logging
import sys
from functools import wraps
from pathlib import Path
from typing import Any

# Import output manager for proper log file placement
from hagent.inou.output_manager import get_output_path


class TransactionLogger:
    """Logger for MCP transactions that creates command-specific log files"""

    def __init__(self):
        """Initialize the transaction logger using output manager"""
        self.loggers = {}

    def _get_logger(self, command_name: str) -> logging.Logger:
        """Get or create a logger for the specified command"""
        if command_name in self.loggers:
            return self.loggers[command_name]

        # Clean command_name for use in filename
        safe_name = command_name.replace('.', '_')
        log_file = get_output_path(f'mcp/{safe_name}.log')

        # Create a new logger
        logger = logging.getLogger(f'hagent-mcp-{safe_name}')
        logger.setLevel(logging.DEBUG)

        # Clear any existing handlers
        logger.handlers = []

        # Add file handler
        # Ensure parent directory exists
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Store and return logger
        self.loggers[command_name] = logger
        return logger

    def log_transaction(self, command_name: str, request: Any, response: Any):
        """Log a transaction for the given command"""
        logger = self._get_logger(command_name)
        timestamp = datetime.datetime.now().isoformat()

        logger.info(f'--- TRANSACTION BEGIN [{timestamp}] ---')
        logger.info(f'REQUEST: {json.dumps(request, indent=2, default=str)}')
        logger.info(f'RESPONSE: {json.dumps(response, indent=2, default=str)}')
        logger.info(f'--- TRANSACTION END [{timestamp}] ---\n')


def setup_mcp_server_logging():
    """Setup logging for MCP server debugging"""
    log_file = get_output_path('hagent_mcp_server.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stderr)],
    )
    return logging.getLogger('hagent-mcp-server')


def setup_raw_logger():
    """Setup a logger for raw stdin/stdout traffic"""
    raw_logger = logging.getLogger('hagent-mcp-raw')
    raw_logger.setLevel(logging.DEBUG)

    # Clear any existing handlers
    raw_logger.handlers = []

    # Add file handler using output manager
    raw_log_file = get_output_path('mcp/raw_mcp_io.log')
    # Ensure parent directory exists
    Path(raw_log_file).parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(raw_log_file)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    raw_logger.addHandler(handler)

    # Also add stderr handler for immediate visibility
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    raw_logger.addHandler(console_handler)

    return raw_logger


def create_transaction_logging_decorator(txn_logger: TransactionLogger):
    """Create a decorator for tool functions to log transactions"""

    def log_transactions(func):
        """Decorator to log tool transactions"""

        @wraps(func)
        def wrapper(*args, **kwargs):
            command_name = getattr(func, '__name__', 'unknown')
            request = {'name': command_name, 'args': args, 'kwargs': kwargs}

            try:
                result = func(*args, **kwargs)
                txn_logger.log_transaction(command_name, request, result)
                return result
            except Exception as e:
                error_response = {'error': str(e), 'type': type(e).__name__}
                txn_logger.log_transaction(command_name, request, error_response)
                raise

        return wrapper

    return log_transactions
