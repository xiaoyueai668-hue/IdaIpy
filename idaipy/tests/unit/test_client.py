"""Unit tests for IdaIpyClient."""

import os
import pytest
from idaipy.client import IdaIpyClient


class TestIdaIpyClientInit:
    """Test IdaIpyClient initialization."""

    def test_default_values(self):
        """Test default host and port."""
        c = IdaIpyClient()
        assert c.host == "127.0.0.1"
        assert c.port == 7123
        assert c.timeout == 600

    def test_explicit_values(self):
        """Test explicit host and port."""
        c = IdaIpyClient(host="192.168.1.1", port=8080, timeout=120)
        assert c.host == "192.168.1.1"
        assert c.port == 8080
        assert c.timeout == 120

    def test_env_var_host(self, monkeypatch):
        """Test IDAIPY_HOST environment variable."""
        monkeypatch.setenv("IDAIPY_HOST", "10.0.0.1")
        c = IdaIpyClient()
        assert c.host == "10.0.0.1"

    def test_env_var_port(self, monkeypatch):
        """Test IDAIPY_PORT environment variable."""
        monkeypatch.setenv("IDAIPY_PORT", "9999")
        c = IdaIpyClient()
        assert c.port == 9999

    def test_env_var_timeout(self, monkeypatch):
        """Test IDAIPY_TIMEOUT environment variable."""
        monkeypatch.setenv("IDAIPY_TIMEOUT", "300")
        c = IdaIpyClient()
        assert c.timeout == 300

    def test_explicit_overrides_env(self, monkeypatch):
        """Test that explicit params override environment variables."""
        monkeypatch.setenv("IDAIPY_HOST", "10.0.0.1")
        monkeypatch.setenv("IDAIPY_PORT", "9999")
        c = IdaIpyClient(host="192.168.1.1", port=8080)
        assert c.host == "192.168.1.1"
        assert c.port == 8080

    def test_workspace_param(self):
        """Test workspace parameter."""
        c = IdaIpyClient(workspace="/path/to/workspace")
        assert c.workspace == "/path/to/workspace"

    def test_retry_param(self):
        """Test retry parameter."""
        c = IdaIpyClient(retry=5)
        assert c._retry == 5
