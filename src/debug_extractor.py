import sys
import time
import logging
sys.path.append(r"c:\Users\Soham\OneDrive\Documents\python\app.1\src")
from feature_extractor import URLFeatureExtractor

logging.basicConfig(level=logging.DEBUG)
url = 'https://example.com'
extractor = URLFeatureExtractor()

start = time.time()
print('Calling _get_domain_features')
try:
    t0 = time.time()
    df = extractor._get_domain_features(url)
    print('domain_features:', df, 'took', time.time()-t0)
except Exception as e:
    print('domain error', e)

print('Calling _get_content_features')
try:
    t0 = time.time()
    cf = extractor._get_content_features(url)
    print('content_features:', cf, 'took', time.time()-t0)
except Exception as e:
    print('content error', e)

print('Calling _get_ssl_features')
try:
    t0 = time.time()
    sf = extractor._get_ssl_features(url)
    print('ssl_features:', sf, 'took', time.time()-t0)
except Exception as e:
    print('ssl error', e)

print('Total', time.time()-start)
