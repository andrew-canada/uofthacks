const { randomUUID } = require('crypto');

const proposals = new Map();

function createId() {
  if (randomUUID) {
    return randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function createProposal(data) {
  const id = createId();
  const record = {
    id,
    status: 'pending',
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    ...data
  };

  proposals.set(id, record);
  return record;
}

function getProposal(id) {
  return proposals.get(id);
}

function updateProposal(id, updates) {
  const existing = proposals.get(id);
  if (!existing) {
    return null;
  }

  const updated = {
    ...existing,
    ...updates,
    updatedAt: new Date().toISOString()
  };
  proposals.set(id, updated);
  return updated;
}

module.exports = {
  createProposal,
  getProposal,
  updateProposal
};
