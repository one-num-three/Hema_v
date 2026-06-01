---
name: freedomain
description: Research and guide users through DigitalPlatDev/FreeDomain, DigitalPlat FreeDomain, and similar free-domain questions. Use when users ask whether FreeDomain is free for ordinary people, whether it works without a VPN in mainland China, what domains are available, how to register or configure DNS/Cloudflare/GitHub Pages, or whether it is safe enough for a project.
---

# DigitalPlat FreeDomain Guide

Use this skill to answer practical questions about DigitalPlatDev/FreeDomain and to walk a user through setup.

## First verify current status

Free domain platforms change policies quickly. Before giving a firm answer, check the current official sources when web access is available:

- GitHub repo: https://github.com/DigitalPlatDev/FreeDomain
- Dashboard: https://dash.domain.digitalplat.org/
- Tutorial index: https://github.com/DigitalPlatDev/FreeDomain/blob/main/documents/tutorial/index.md
- Getting started: https://github.com/DigitalPlatDev/FreeDomain/blob/main/documents/tutorial/getting-started/index.md
- Account registration: https://github.com/DigitalPlatDev/FreeDomain/blob/main/documents/tutorial/getting-started/1.1-register-account.md
- DNS hosting: https://github.com/DigitalPlatDev/FreeDomain/blob/main/documents/tutorial/getting-started/1.2-dns-hosting.md
- FAQ: https://github.com/DigitalPlatDev/FreeDomain/blob/main/documents/domains/faq.md

If sources differ, prefer the dashboard and the latest GitHub documentation. Mention the check date.

## Quick answers

- **Is it free for ordinary people?** Usually yes, according to the project README: it offers free domain names for individuals and organizations. The FAQ currently says the default limit is 1 domain per user account.
- **Is starring the GitHub repo required?** No. The FAQ says stars are appreciated, not required.
- **What suffixes are listed?** The README currently lists `.dpdns.org`, `.us.kg`, `.qzz.io`, `.xx.kg`, and `.qd.je`. Availability can change.
- **Is it a normal paid registrar domain?** Treat it as a free managed namespace/subdomain-style service, not the same ownership guarantees as a paid domain from a registrar.
- **Can it use Cloudflare?** Yes. The FAQ says Cloudflare is supported, and the tutorial recommends Cloudflare for beginners.
- **Can it use other DNS providers?** Yes. The FAQ says it works with virtually any DNS management system by setting provided NS records or custom nameservers.

## Mainland China access guidance

Do not promise "no VPN needed" unless the user or a live test from their target network confirms it.

Give a careful answer:

- GitHub is often reachable from mainland China but can be slow or unstable depending on ISP, region, and time.
- The DigitalPlat dashboard and Cloudflare dashboard may behave differently from GitHub. Access can be affected by DNS, TLS, anti-bot checks, or regional network conditions.
- If the user is in mainland China, ask them to test these URLs directly on their own network before relying on the service:
  - https://github.com/DigitalPlatDev/FreeDomain
  - https://dash.domain.digitalplat.org/
  - https://dash.cloudflare.com/
- If they cannot open the dashboard without a proxy, they may still be able to read GitHub docs but cannot complete registration or DNS changes comfortably.

When asked "domestic access/no VPN?", answer as a probability and verification plan, not a guarantee.

## Setup workflow

1. Open the dashboard registration page: `https://dash.domain.digitalplat.org/auth/register`.
2. Create a DigitalPlat account with a username, strong password, and real email.
3. Provide the required WHOIS information: name or organization, address, and phone number.
4. Read and accept Terms of Service, Privacy Policy, and Acceptable Use Policy.
5. Claim an available domain suffix from the dashboard.
6. Choose DNS hosting. For beginners, recommend Cloudflare's free plan.
7. Add the domain to Cloudflare, choose the Free plan, and copy Cloudflare's two assigned nameservers.
8. Return to DigitalPlat, open domain settings, replace nameservers with the Cloudflare nameservers, and save.
9. Wait for DNS propagation. The tutorial says it usually takes minutes but can take up to 24 hours.
10. Add DNS records in Cloudflare:
    - `A` or `AAAA` to point to an IP address.
    - `CNAME` to point to another hostname such as GitHub Pages or a hosting provider.
    - `TXT` for service verification.

## GitHub Pages example

For a GitHub Pages site:

1. In Cloudflare DNS, create a `CNAME` record for the desired host, for example `www.example.dpdns.org`, pointing to `<username>.github.io`.
2. In the GitHub repository, set Pages custom domain to the same hostname.
3. Wait for DNS and certificate provisioning.
4. Keep Cloudflare proxy off initially for troubleshooting; enable proxy only after GitHub Pages works and HTTPS is stable.

## Risk framing

Be candid about tradeoffs:

- Free domains are good for experiments, demos, student projects, internal tools, hobby sites, and low-risk projects.
- Avoid using free managed namespaces for a serious business brand, long-term SEO asset, payment flows, or anything where losing the domain would be expensive.
- Policies, limits, suffix availability, abuse controls, and service continuity may change.
- WHOIS details may be public unless privacy protection is enabled in the dashboard.
- Users must follow acceptable-use rules; abuse can lead to suspension.

## Answer style

When responding to users:

- Separate confirmed facts from assumptions.
- Include the official links they need.
- For China access, say "I cannot guarantee from outside your ISP; here is how to test" unless tested from the user's own network.
- If they ask whether to use it, give a recommendation based on project risk: "fine for testing" vs "buy a paid domain".
