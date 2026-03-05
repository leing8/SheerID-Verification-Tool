"""代理字符串验证与解析测试

覆盖:
- URL 格式 (http://, socks5://)
- 带认证
- host:port
- host:port:user:pass
- user:pass@host:port
- 无效格式
"""

import pytest
from proxy_checker.models import ProxyInfo
from proxy_checker.validator import parse_proxy


class TestParseUrlFormat:
    """URL 格式解析"""

    def test_http_url(self) -> None:
        """http://host:port"""
        result = parse_proxy("http://proxy.example:8080")
        assert isinstance(result, ProxyInfo)
        assert result.host == "proxy.example"
        assert result.port == 8080
        assert result.protocol == "http"

    def test_socks5_url(self) -> None:
        """socks5://host:port"""
        result = parse_proxy("socks5://proxy.example:1080")
        assert result.protocol == "socks5"
        assert result.port == 1080

    def test_url_with_auth(self) -> None:
        """http://user:pass@host:port"""
        result = parse_proxy("http://myuser:mypass@proxy.example:8080")
        assert result.host == "proxy.example"
        assert result.port == 8080
        assert result.username == "myuser"
        assert result.password == "mypass"


class TestHostPortFormat:
    """host:port 格式"""

    def test_simple_host_port(self) -> None:
        """host:port"""
        result = parse_proxy("proxy.example:8080")
        assert result.host == "proxy.example"
        assert result.port == 8080

    def test_ip_port(self) -> None:
        """IP:port"""
        result = parse_proxy("192.168.1.100:3128")
        assert result.host == "192.168.1.100"
        assert result.port == 3128


class TestHostPortUserPass:
    """host:port:user:pass 格式"""

    def test_four_part_format(self) -> None:
        """host:port:user:pass"""
        result = parse_proxy("proxy.example:8080:myuser:mypass")
        assert result.host == "proxy.example"
        assert result.port == 8080
        assert result.username == "myuser"
        assert result.password == "mypass"


class TestUserPassAtHostPort:
    """user:pass@host:port 格式"""

    def test_at_sign_format(self) -> None:
        """user:pass@host:port"""
        result = parse_proxy("myuser:mypass@proxy.example:8080")
        assert result.host == "proxy.example"
        assert result.username == "myuser"


class TestInvalidFormats:
    """无效格式"""

    def test_empty_string(self) -> None:
        assert parse_proxy("") is None

    def test_none_input(self) -> None:
        assert parse_proxy(None) is None

    def test_whitespace_only(self) -> None:
        assert parse_proxy("   ") is None

    def test_single_word(self) -> None:
        """单个字符串无端口"""
        assert parse_proxy("justahostname") is None

    def test_three_parts(self) -> None:
        """三段格式不支持"""
        assert parse_proxy("a:b:c") is None


class TestEdgeCases:
    """边界情况"""

    def test_strips_whitespace(self) -> None:
        """自动去除首尾空格"""
        result = parse_proxy("  proxy.example:8080  ")
        assert result.host == "proxy.example"

    def test_frozen_dataclass(self) -> None:
        """ProxyInfo 是 frozen 的"""
        result = parse_proxy("proxy.example:8080")
        with pytest.raises(AttributeError):
            result.host = "modified"  # type: ignore[misc]
