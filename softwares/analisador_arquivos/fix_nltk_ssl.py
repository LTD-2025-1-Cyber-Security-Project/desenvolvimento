import ssl
import nltk

# Create an SSL context that doesn't verify certificates
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download NLTK data
nltk.download('punkt')
nltk.download('stopwords')

print("NLTK data downloaded successfully!")