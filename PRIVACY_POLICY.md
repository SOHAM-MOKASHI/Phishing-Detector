# Privacy Policy — Phishing Detector

Last updated: 2025-12-27

This privacy policy explains what data the Phishing Detector service and browser
extension collect and how that data is used.

1. What we collect
- URLs submitted for inspection: the extension sends the current page URL to the
  backend API so the model can analyze features and respond with a phishing
  assessment (is_phishing, confidence, risk factors). No additional browsing
  history or personally identifiable information is collected by default.

2. How we use the data
- URL features are only used to compute the phishing prediction and to produce
  risk explanations. The service does not use URLs for advertising or sell them
  to third parties.

3. Retention
- The hosted API may log requests for debugging and abuse prevention. Logs are
  retained for a limited time and are not shared externally. If you host your
  own instance, retention is under your control.

4. Security
- The API supports an API key header (`x-api-key`). When hosting publicly,
  enable the API key and serve the API over HTTPS. Do not embed public keys in
  published extensions — instead provide per-deployment keys via the extension
  options.

5. Third-party services
- If you deploy on a hosting provider (Render, Railway, etc.), the provider may
  have its own logs/analytics. Review the provider's privacy policies.

6. Contact
- For questions about privacy and security, contact the project maintainer via
  the repository issues page.
