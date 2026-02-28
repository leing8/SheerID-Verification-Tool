"""
test_validator.py — 代理字符串解析测试

测试 parse_proxy 函数对各种代理格式的解析能力和边界情况。
所有测试均为纯本地逻辑，不涉及网络请求。
"""

import pytest

from proxy_checker.validator import parse_proxy


class TestParseProxyWithProtocol:
    """带协议前缀的代理解析"""

    def test_http_host_port(self):
        """http://host:port"""
        info = parse_proxy("http://proxy.example.com:8080")
        assert info is not None
        assert info.protocol == "http"
        assert info.host == "proxy.example.com"
        assert info.port == 8080
        assert info.username is None
        assert info.password is None

    def test_http_with_auth(self):
        """http://user:pass@host:port"""
        info = parse_proxy("http://admin:secret@proxy.example.com:3128")
        assert info is not None
        assert info.protocol == "http"
        assert info.host == "proxy.example.com"
        assert info.port == 3128
        assert info.username == "admin"
        assert info.password == "secret"

    def test_https_proxy(self):
        """https://host:port"""
        info = parse_proxy("https://secure.proxy.com:443")
        assert info is not None
        assert info.protocol == "https"
        assert info.host == "secure.proxy.com"
        assert info.port == 443

    def test_socks5_proxy(self):
        """socks5://host:port"""
        info = parse_proxy("socks5://socks.proxy.com:1080")
        assert info is not None
        assert info.protocol == "socks5"
        assert info.host == "socks.proxy.com"
        assert info.port == 1080

    def test_socks5_with_auth(self):
        """socks5://user:pass@host:port"""
        info = parse_proxy("socks5://user:pwd@socks.proxy.com:1080")
        assert info is not None
        assert info.protocol == "socks5"
        assert info.username == "user"
        assert info.password == "pwd"


class TestParseProxyWithoutProtocol:
    """不带协议前缀的代理解析"""

    def test_host_port(self):
        """host:port (两段式)"""
        info = parse_proxy("192.168.1.100:8080")
        assert info is not None
        assert info.protocol == "http"
        assert info.host == "192.168.1.100"
        assert info.port == 8080
        assert info.username is None

    def test_host_port_user_pass(self):
        """host:port:user:pass (四段式)"""
        info = parse_proxy("192.168.1.100:8080:admin:secret")
        assert info is not None
        assert info.protocol == "http"
        assert info.host == "192.168.1.100"
        assert info.port == 8080
        assert info.username == "admin"
        assert info.password == "secret"

    def test_user_pass_at_host_port(self):
        """user:pass@host:port (含 @ 无协议)"""
        info = parse_proxy("admin:secret@proxy.example.com:8080")
        assert info is not None
        assert info.host == "proxy.example.com"
        assert info.port == 8080
        assert info.username == "admin"
        assert info.password == "secret"


class TestParseProxyEdgeCases:
    """边界与异常情况"""

    @pytest.mark.parametrize("input_str", [
        None,
        "",
        "   ",
        "\t\n",
    ])
    def test_empty_or_whitespace_returns_none(self, input_str):
        """空、纯空白 → None"""
        result = parse_proxy(input_str) if input_str is not None else parse_proxy("")
        assert result is None

    def test_invalid_port_returns_none(self):
        """无效端口号 → None"""
        result = parse_proxy("host.com:abc")
        assert result is None

    def test_three_parts_no_at_returns_none(self):
        """三段式 (host:port:extra) 无 @ → None"""
        result = parse_proxy("host:8080:extra")
        assert result is None

    def test_whitespace_trimmed(self):
        """前后空白应被清理"""
        info = parse_proxy("  http://proxy.com:8080  ")
        assert info is not None
        assert info.host == "proxy.com"

    def test_url_preserved(self):
        """ProxyInfo.url 保留完整代理地址"""
        info = parse_proxy("http://user:pass@proxy.com:3128")
        assert "proxy.com:3128" in info.url
        assert "user:pass" in info.url
