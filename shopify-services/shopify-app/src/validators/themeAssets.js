const DEFAULT_MAX_BYTES = Number(process.env.THEME_ASSET_MAX_BYTES || 500000);
const ALLOWED_PREFIXES = [
  'layout/',
  'templates/',
  'sections/',
  'snippets/',
  'assets/',
  'config/',
  'locales/'
];

function validateAssetKey(key) {
  if (typeof key !== 'string' || key.trim() === '') {
    return 'Asset key must be a non-empty string.';
  }

  if (key.startsWith('/') || key.includes('..')) {
    return `Invalid asset key: ${key}`;
  }

  if (!ALLOWED_PREFIXES.some((prefix) => key.startsWith(prefix))) {
    return `Asset key must start with one of: ${ALLOWED_PREFIXES.join(', ')}`;
  }

  return null;
}

function validateAssetValue(key, value) {
  if (typeof value !== 'string') {
    return `Asset value for ${key} must be a string.`;
  }

  if (Buffer.byteLength(value, 'utf8') > DEFAULT_MAX_BYTES) {
    return `Asset ${key} exceeds ${DEFAULT_MAX_BYTES} bytes.`;
  }

  if (key.endsWith('.json')) {
    try {
      JSON.parse(value);
    } catch (error) {
      return `Asset ${key} contains invalid JSON.`;
    }
  }

  return null;
}

function validateAssetsMap(files) {
  if (!files || typeof files !== 'object' || Array.isArray(files)) {
    throw new Error('files must be an object keyed by asset path.');
  }

  const errors = [];

  for (const [key, value] of Object.entries(files)) {
    const keyError = validateAssetKey(key);
    if (keyError) {
      errors.push(keyError);
      continue;
    }

    const valueError = validateAssetValue(key, value);
    if (valueError) {
      errors.push(valueError);
    }
  }

  if (errors.length > 0) {
    throw new Error(errors.join(' '));
  }

  return true;
}

module.exports = {
  validateAssetsMap
};
