// Real vulnerable microservice: Node.js / Express Checkout API.
// Contains 3 genuine bugs: SQL Injection (CWE-89), OS Command Injection (CWE-78),
// and a Hardcoded Live Secret (CWE-798). Used by @recon/@specter/@forge/@warden demos.
const express = require("express");
const { exec } = require("child_process");

const router = express.Router();

// BUG 3 (CWE-798 HIGH): Live production Stripe secret hardcoded in source control
const STRIPE_SECRET = "[SECURITY_DATA]";

router.get("/orders/:userId", async (req, res) => {
  // BUG 1 (CWE-89 CRITICAL): User input interpolated straight into SQL string
  const rows = await req.db.query(`SELECT * FROM orders WHERE user_id = '${req.params.userId}'`);
  res.json(rows);
});

router.post("/invoice/archive", (req, res) => {
  // BUG 2 (CWE-78 CRITICAL): User-controlled filename reaches a shell command
  exec("tar -czf /tmp/inv.tgz /var/invoices/" + req.body.filename, (err) => {
    if (err) return res.status(500).json({ error: "archive failed" });
    res.json({ ok: true, key: STRIPE_SECRET.slice(0, 7) });
  });
});

module.exports = router;
