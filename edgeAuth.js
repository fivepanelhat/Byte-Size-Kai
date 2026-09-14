// Public edge auth disabled — commercial-track / private.
// TLS/JWT edge-node auth method packs are not published on public GitHub.
// See README.md and PUBLIC_POSTURE.md.

module.exports = {
  issueEdgeToken: (_req, res) => {
    res.status(501).send("Public edge auth is disabled. Commercial-track / private.");
  },
  authenticateEdgeNode: (_req, res) => {
    res.sendStatus(501);
  },
};
