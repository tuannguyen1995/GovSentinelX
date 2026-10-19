# Portal Submission Draft — GovSentinelX

**Portal Track:** Builder  
**Contribution Type:** Intelligent Contracts  
**Network:** studionet (Chain ID: 61999)  
**Contract Address:** `0x9ccC975433bfACA58E82a7F8D72b617c484f6860`  
**Deployer Address:** `0x33Ce552FBA45C17478aBc5778bDbc2c86E9a9A05`  
**Transaction Hash:** `0x29ec353949adf9d4d0c94a560555d82be5e14e14b1b5acd3b45aaee23608c390`  
**Evidence URL 1:** `https://explorer-studio.genlayer.com/address/0x9ccC975433bfACA58E82a7F8D72b617c484f6860`  

---

### Title
```
GovSentinelX — AI-Driven DAO Proposal Impact & Compliance Scraper
```

### One-liner (< 180 characters)
```
Autonomous protocol scraping and evaluating DAO governance proposals on-chain for financial impact, security vulnerabilities, and compliance via GenLayer LLM validator consensus.
```

### Notes / Description (< 1000 characters)
```
GovSentinelX is an autonomous DAO governance proposal impact and compliance scraper on GenLayer. It protects decentralized treasuries and DAO delegates against malicious payloads, hidden treasury drains, and governance backdoors concealed within lengthy governance proposals.

Users submit proposal links from Snapshot, Tally, or DAO forums. GenLayer validators autonomously scrape live proposal content on-chain using gl.nondet.web.render with hardened anti-SSRF protections. An Optimistic Democracy LLM jury analyzes financial impact, tokenomic changes, and contract safety, enforcing discrete semantic consensus across sentiment categories (FAVORABLE, CONTROVERSIAL, HIGH_RISK, FAILED_EVIDENCE) and scoring risk from 0 to 100.

Key Highlights:
- 100% On-chain execution: Scrapes live governance text and audits proposals without off-chain oracles.
- GenVM Storage Compliant: Strict adherence to GenVM typing (bigint scores, no bare int).
- 10/10 passing gltest unit tests. Deployed & verified on Studionet.
```

### Steward Response (Joaquin)
```
Dear Joaquin,

We are pleased to submit GovSentinelX for the GenLayer Builder Track:
1. Core Decision on GenVM: Web scraping of live DAO proposals (Snapshot/Tally/Forums) and LLM-driven impact & compliance audits execute autonomously inside the Intelligent Contract via gl.nondet.web.render and gl.vm.run_nondet validator consensus.
2. Robust Edge-Case Handling: 404 pages, offline forums, and unparseable contents are gracefully classified as FAILED_EVIDENCE, preventing state corruption. Anti-SSRF guards strictly protect against internal subnet probing.
3. Strict Storage Compliance: Full conformance with GenVM storage laws (R14) using @allow_storage @dataclass with bigint fields for risk_score, counters, and timestamps.
4. Comprehensive Testing & Verification: 10/10 automated gltest unit tests passing across all analysis modes and edge cases. The contract is finalized and verified on Studionet at address 0x9ccC975433bfACA58E82a7F8D72b617c484f6860.
```
