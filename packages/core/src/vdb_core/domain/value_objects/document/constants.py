"""Document-related domain constants."""

# Max fragment size: 100 MB
# Fragments larger than this are rejected during upload
MAX_FRAGMENT_SIZE_BYTES = 100 * 1024 * 1024

# Name constraints (used by DocumentName)
MIN_NAME_LENGTH = 1
MAX_NAME_LENGTH = 50
