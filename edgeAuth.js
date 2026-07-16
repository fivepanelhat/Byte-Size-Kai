const jwt = require('jsonwebtoken');
const fs = require('fs');

// Load the keys from the secure local filesystem
const privateKey = fs.readFileSync('./tls-certs/private-key.pem');
const publicKey = fs.readFileSync('./tls-certs/public-key.pem');

// Mock function representing database lookup/validation
function validateLocalHardware(deviceId, hardwareSecret) {
 // Implement your hardware authentication database logic here
 return deviceId && hardwareSecret === 'super_secret_hardware_key'; // pragma: allowlist secret
}

module.exports = {
 // 1. Issuing the Token (When ESP32 connects)
 issueEdgeToken: (req, res) => {
 const { deviceId, hardwareSecret } = req.body;
 
 // Validate against your local edge database (No Cloud required)
 if (validateLocalHardware(deviceId, hardwareSecret)) {
 
 // Sign the token using ES256
 const token = jwt.sign(
 { edgeNode: deviceId, role: 'sensor' }, 
 privateKey, 
 { algorithm: 'ES256', expiresIn: '2h' } // Short lifespan for security
 );
 
 res.json({ accessToken: token });
 } else {
 res.status(401).send("Rogue node detected.");
 }
 },

 // 2. Verifying the Token (Middleware for your API routes)
 authenticateEdgeNode: (req, res, next) => {
 const token = req.headers['authorization']?.split(' ')[1];
 
 if (!token) return res.sendStatus(401);

 // Verify using the public key
 jwt.verify(token, publicKey, { algorithms: ['ES256'] }, (err, node) => {
 if (err) return res.sendStatus(403);
 req.node = node;
 next();
 });
 }
};
