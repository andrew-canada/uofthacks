const suggestions = [];

function getAll() {
  return suggestions;
}

function addSuggestion(suggestion) {
  suggestions.push(suggestion);
  return suggestion;
}

function addMany(newSuggestions) {
  suggestions.push(...newSuggestions);
  return newSuggestions;
}

function findById(id) {
  return suggestions.find((suggestion) => suggestion.id === id);
}

function removeById(id) {
  const index = suggestions.findIndex((suggestion) => suggestion.id === id);
  if (index === -1) {
    return null;
  }

  return suggestions.splice(index, 1)[0];
}

module.exports = {
  getAll,
  addSuggestion,
  addMany,
  findById,
  removeById
};
