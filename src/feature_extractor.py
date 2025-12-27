import re
import logging
import whois
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import datetime
import ssl
import socket
from tld import get_tld

class URLFeatureExtractor:
    def __init__(self):
        self.features = {}
        self.logger = logging.getLogger(__name__)
        self._whois_cache = {}

        # Configure a requests session with retries to reduce intermittent timeouts
        self.session = requests.Session()
        retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def extract_features(self, url):
        """Extract features from URL for phishing detection"""
        try:
            self.features = {
                'url_length': len(url),
                'domain_features': self._get_domain_features(url),
                'url_features': self._get_url_features(url),
                'content_features': self._get_content_features(url),
                'ssl_features': self._get_ssl_features(url)
            }
            return self.features
        except Exception as e:
            print(f"Error extracting features: {str(e)}")
            return None

    def _get_domain_features(self, url):
        """Extract domain-related features"""
        try:
            parsed = urlparse(url)
            hostname = (parsed.hostname or parsed.netloc or '').lower()

            # Basic registered-domain fallback: take last two labels
            parts = hostname.split('.') if hostname else []
            if len(parts) >= 2:
                registered = '.'.join(parts[-2:])
            else:
                registered = hostname

            # Simple cache to avoid repeated WHOIS network calls
            if registered in self._whois_cache:
                w = self._whois_cache[registered]
            else:
                try:
                    w = whois.whois(registered)
                except Exception:
                    w = None
                self._whois_cache[registered] = w

            creation = None
            expiration = None
            has_whois = False
            if w:
                try:
                    creation = getattr(w, 'creation_date', None)
                    expiration = getattr(w, 'expiration_date', None)
                    if isinstance(creation, list) and creation:
                        creation = creation[0]
                    if isinstance(expiration, list) and expiration:
                        expiration = expiration[0]
                    has_whois = bool(getattr(w, 'domain_name', None))
                except Exception:
                    creation = None
                    expiration = None

            domain_age = (datetime.now() - creation).days if creation else -1
            domain_expiry = (expiration - datetime.now()).days if expiration else -1

            return {
                'domain_age': domain_age,
                'domain_expiry': domain_expiry,
                'has_whois': bool(has_whois)
            }
        except:
            return {'domain_age': -1, 'domain_expiry': -1, 'has_whois': False}

    def _get_url_features(self, url):
        """Extract URL-based features"""
        parsed = urlparse(url)
        return {
            'num_dots': url.count('.'),
            'num_digits': len(re.findall(r'\d', url)),
            'num_special_chars': len(re.findall(r'[^a-zA-Z0-9.]', url)),
            'has_ip_address': bool(re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', parsed.netloc)),
            'has_at_symbol': '@' in url,
            'has_double_slash': '//' in parsed.path,
            'has_hex_chars': bool(re.search(r'%[0-9a-fA-F]{2}', url))
        }

    def _get_content_features(self, url):
        """Extract webpage content features"""
        try:
            # Use a short timeout and the session (with retries) to avoid long blocking calls
            headers = {'User-Agent': 'phishing-detector/1.0'}
            response = self.session.get(url, timeout=5, verify=False, headers=headers)
            if response.status_code != 200:
                self.logger.debug(f"Non-200 response fetching {url}: {response.status_code}")
                raise Exception(f"HTTP {response.status_code}")

            soup = BeautifulSoup(response.text, 'html.parser')

            return {
                'num_external_links': len([link for link in soup.find_all('a') if urlparse(link.get('href', '')).netloc != urlparse(url).netloc]),
                'has_form': bool(soup.find_all('form')),
                'has_password_field': bool(soup.find_all('input', {'type': 'password'})),
                'num_iframes': len(soup.find_all('iframe')),
                'has_hidden_element': bool(soup.find_all(style=re.compile(r'display:\s*none')))
            }
        except:
            return {
                'num_external_links': -1,
                'has_form': False,
                'has_password_field': False,
                'num_iframes': -1,
                'has_hidden_element': False
            }

    def _get_ssl_features(self, url):
        """Extract SSL/TLS certificate features"""
        try:
            parsed = urlparse(url)
            host = parsed.hostname or parsed.netloc
            if not host:
                raise ValueError("No host found in URL")

            context = ssl.create_default_context()
            # Use a short timeout on the socket to avoid long waits
            with socket.create_connection((host, 443), timeout=5) as sock:
                with context.wrap_socket(sock, server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
                    not_after = cert.get('notAfter')
                    ssl_days = -1
                    if not_after:
                        try:
                            ssl_days = (datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z') - datetime.now()).days
                        except Exception:
                            # Some certificates may use different formats; ignore parsing errors
                            ssl_days = -1

                    issuer = None
                    try:
                        issuer = cert['issuer'][0][0][1]
                    except Exception:
                        issuer = None

                    return {
                        'has_ssl': True,
                        'ssl_issuer': issuer,
                        'ssl_days_valid': ssl_days
                    }
        except:
            return {'has_ssl': False, 'ssl_issuer': None, 'ssl_days_valid': -1}