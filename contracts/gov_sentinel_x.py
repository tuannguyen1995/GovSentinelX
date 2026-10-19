# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from genlayer import *
from dataclasses import dataclass
import json

try:
    gl.UserError = gl.vm.UserError
except Exception:
    pass


def _addr_str(addr: Address) -> str:
    """Safely format an Address instance into a lowercase hex string."""
    try:
        return addr.as_hex.lower()
    except Exception:
        return str(addr).lower()


def _get_sender() -> Address:
    """Safely obtain transaction sender across GenVM runtime versions."""
    try:
        if hasattr(gl, "message"):
            if hasattr(gl.message, "sender"):
                return gl.message.sender
            if hasattr(gl.message, "sender_address"):
                return gl.message.sender_address
    except Exception:
        pass
    try:
        if hasattr(gl, "message_raw") and isinstance(gl.message_raw, dict):
            s = gl.message_raw.get("from") or gl.message_raw.get("sender")
            if s:
                return Address(str(s))
    except Exception:
        pass
    raise gl.UserError("Cannot resolve sender address.")


def _validate_proposal_url(raw_url: str) -> str:
    """Validate proposal URL and guard against SSRF attack vectors."""
    clean = raw_url.strip()
    if not (clean.startswith("http://") or clean.startswith("https://")):
        raise gl.UserError("Proposal URL must start with http:// or https://")

    clean_lower = clean.lower()
    # Guard against local network SSRF attempts
    for blocked in (
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
        "192.168.",
        "10.",
        "172.16.",
        "169.254.",
    ):
        if blocked in clean_lower:
            raise gl.UserError("Local and private network URLs are prohibited.")

    return clean


@allow_storage
@dataclass
class GovProposal:
    proposal_id: str
    submitter: Address
    proposal_url: str       # Link to Snapshot/Forum governance proposal
    title: str              # Proposal title or identifier
    status: str             # "PENDING", "ANALYZED", "FAILED_EVIDENCE"
    risk_score: bigint      # 0 to 100 risk assessment score (compliant with GenVM R14: no bare int in storage)
    sentiment: str          # "FAVORABLE", "CONTROVERSIAL", "HIGH_RISK", "FAILED_EVIDENCE"
    summary_report: str     # AI structured impact and compliance summary
    created_at: bigint
    resolved_at: bigint


class Contract(gl.Contract):
    """
    GovSentinelX: Autonomous DAO Proposal Impact & Compliance Scraper on GenLayer
    Track: AI Governance / Subjective Consensus / Autonomous Security Auditing
    """
    owner: Address
    proposal_count: bigint
    proposals: TreeMap[str, GovProposal]
    analyzed_count: bigint
    high_risk_count: bigint
    favorable_count: bigint
    controversial_count: bigint
    failed_evidence_count: bigint

    def __init__(self):
        # GenVM automatically initializes TreeMap storage fields to empty.
        self.owner = _get_sender()
        self.proposal_count = bigint(0)
        self.analyzed_count = bigint(0)
        self.high_risk_count = bigint(0)
        self.favorable_count = bigint(0)
        self.controversial_count = bigint(0)
        self.failed_evidence_count = bigint(0)

    def _get_current_timestamp(self) -> bigint:
        """Derive trusted deterministic execution timestamp from GenLayer transaction context."""
        try:
            from datetime import datetime
            dt_raw = getattr(gl.message, "datetime", None)
            if dt_raw is None and hasattr(gl, "message_raw") and isinstance(gl.message_raw, dict):
                dt_raw = gl.message_raw.get("datetime")
            if dt_raw:
                dt_str = str(dt_raw).strip().replace("Z", "+00:00")
                dt = datetime.fromisoformat(dt_str)
                ts = int(dt.timestamp())
                if ts > 0:
                    return bigint(ts)
        except Exception:
            pass
        try:
            if hasattr(gl, "block") and hasattr(gl.block, "timestamp"):
                ts = int(gl.block.timestamp)
                if ts > 0:
                    return bigint(ts)
        except Exception:
            pass
        return bigint(0)

    def _parse_llm_json(self, text: str) -> dict:
        """Safely parse LLM responses, stripping markdown wrappers if present."""
        try:
            cleaned = str(text).strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            return json.loads(cleaned.strip())
        except Exception as e:
            return {
                "risk_score": 0,
                "sentiment": "FAILED_EVIDENCE",
                "summary_report": f"Analysis JSON parse error: {str(e)[:100]}"
            }

    @gl.public.write
    def submit_proposal(self, title: str, proposal_url: str) -> str:
        """
        Submit a DAO governance proposal link for autonomous impact and compliance analysis.
        """
        clean_title = title.strip()
        clean_url = _validate_proposal_url(proposal_url)

        if len(clean_title) < 5:
            raise gl.UserError("Proposal title is too short.")

        self.proposal_count += bigint(1)
        pid = str(self.proposal_count)
        now_ts = self._get_current_timestamp()

        self.proposals[pid] = GovProposal(
            proposal_id=pid,
            submitter=_get_sender(),
            proposal_url=clean_url,
            title=clean_title,
            status="PENDING",
            risk_score=bigint(0),
            sentiment="PENDING",
            summary_report="Awaiting validator governance analysis.",
            created_at=now_ts if now_ts > bigint(0) else self.proposal_count,
            resolved_at=bigint(0)
        )
        return pid

    @gl.public.write
    def analyze_proposal(self, proposal_id: str) -> None:
        """
        Validators scrape the governance proposal URL on-chain and utilize GenLayer Optimistic Democracy
        LLM jury consensus to evaluate financial risk, smart contract impact, and compliance.
        """
        if proposal_id not in self.proposals:
            raise gl.UserError("Proposal not found.")

        prop = self.proposals[proposal_id]
        if prop.status != "PENDING":
            raise gl.UserError("Proposal has already been analyzed.")

        title_local = str(prop.title)
        url_local = str(prop.proposal_url)

        def leader_fn():
            web_content = ""
            try:
                res = gl.nondet.web.render(url_local, mode="text")
                if hasattr(res, "content"):
                    web_content = res.content
                elif isinstance(res, dict) and "body" in res:
                    web_content = res["body"]
                else:
                    web_content = str(res)
            except Exception:
                web_content = ""

            lower_web = web_content[:500].lower() if web_content else ""
            if len(web_content.strip()) < 15 or "404 not found" in lower_web or "error" in lower_web:
                return {
                    "risk_score": 0,
                    "sentiment": "FAILED_EVIDENCE",
                    "summary_report": "Proposal URL is offline, blank, or inaccessible."
                }

            snippet = web_content[:4000]

            prompt = f"""You are an expert DAO Governance Analyst, Risk Officer, and Smart Contract Auditor.
Analyze the following governance proposal for financial impact, protocol risks, treasury drainage, backdoor governance changes, and regulatory compliance.

PROPOSAL TITLE: {title_local}

SCRAPED PROPOSAL CONTENT:
\"\"\"
{snippet}
\"\"\"

ANALYSIS RULES:
- Assign a risk_score from 0 to 100 (0 = completely safe/standard, 100 = extreme centralization or malicious risk).
- Determine sentiment: "FAVORABLE" (low risk, clear protocol benefits), "CONTROVERSIAL" (mixed community impact or significant tokenomic shifts), or "HIGH_RISK" (severe financial, technical, or security threats).
- If content is unparsable or contradictory, set sentiment to "FAILED_EVIDENCE".
- Provide a concise summary report (max 250 characters).

OUTPUT FORMAT:
Respond ONLY with a VALID JSON object (no markdown, no backticks):
{{
  "risk_score": <integer 0-100>,
  "sentiment": "FAVORABLE" | "CONTROVERSIAL" | "HIGH_RISK" | "FAILED_EVIDENCE",
  "summary_report": "<concise professional analysis summary>"
}}"""

            try:
                raw_res = gl.nondet.exec_prompt(prompt, response_format="json")
                parsed = None
                if isinstance(raw_res, dict):
                    parsed = raw_res
                elif hasattr(raw_res, "content") and isinstance(raw_res.content, dict):
                    parsed = raw_res.content
                else:
                    text = raw_res.content if hasattr(raw_res, "content") else str(raw_res)
                    cleaned = str(text).strip()
                    if cleaned.startswith("```json"):
                        cleaned = cleaned[7:]
                    elif cleaned.startswith("```"):
                        cleaned = cleaned[3:]
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3]
                    parsed = json.loads(cleaned.strip())

                risk = int(parsed.get("risk_score", 50))
                risk = max(0, min(100, risk))
                sentiment = str(parsed.get("sentiment", "CONTROVERSIAL")).strip().upper()
                if sentiment not in ("FAVORABLE", "CONTROVERSIAL", "HIGH_RISK", "FAILED_EVIDENCE"):
                    sentiment = "CONTROVERSIAL"
                summary = str(parsed.get("summary_report", "Analyzed."))[:250]

                return {
                    "risk_score": risk,
                    "sentiment": sentiment,
                    "summary_report": summary
                }
            except Exception as e:
                return {
                    "risk_score": 0,
                    "sentiment": "FAILED_EVIDENCE",
                    "summary_report": f"Analysis error: {str(e)[:100]}"
                }

        def validator_fn(leader_res) -> bool:
            if not isinstance(leader_res, gl.vm.Return):
                return False
            leader = leader_res.calldata
            if not isinstance(leader, dict) or "sentiment" not in leader:
                return False

            valid_sentiments = ("FAVORABLE", "CONTROVERSIAL", "HIGH_RISK", "FAILED_EVIDENCE")
            l_sentiment = str(leader.get("sentiment", "")).strip().upper()
            if l_sentiment not in valid_sentiments:
                return False

            mine = leader_fn()
            m_sentiment = str(mine.get("sentiment", "")).strip().upper()

            # DISCRETE EQUIVALENCE: validators must agree on the core sentiment category
            if l_sentiment != m_sentiment:
                return False

            # If both analyzed, verify risk scores are within acceptable tolerance window (<= 20 points)
            if l_sentiment != "FAILED_EVIDENCE":
                l_risk = int(leader.get("risk_score", 0))
                m_risk = int(mine.get("risk_score", 0))
                if abs(l_risk - m_risk) > 20:
                    return False

            return True

        adjudication_res = gl.vm.run_nondet(leader_fn, validator_fn)
        if isinstance(adjudication_res, dict):
            final_res = adjudication_res
        else:
            final_res = self._parse_llm_json(str(adjudication_res))

        risk = int(final_res.get("risk_score", 0))
        risk_clamped = max(0, min(100, risk))
        sentiment = str(final_res.get("sentiment", "FAILED_EVIDENCE")).strip().upper()
        summary = str(final_res.get("summary_report", "Processed."))

        prop.risk_score = bigint(risk_clamped)
        prop.sentiment = sentiment
        prop.summary_report = summary
        prop.status = "ANALYZED" if sentiment != "FAILED_EVIDENCE" else "FAILED_EVIDENCE"
        now_ts = self._get_current_timestamp()
        prop.resolved_at = now_ts if now_ts > bigint(0) else self.proposal_count
        self.proposals[proposal_id] = prop

        # Update statistical counters
        if prop.status == "ANALYZED":
            self.analyzed_count += bigint(1)
            if sentiment == "HIGH_RISK":
                self.high_risk_count += bigint(1)
            elif sentiment == "FAVORABLE":
                self.favorable_count += bigint(1)
            elif sentiment == "CONTROVERSIAL":
                self.controversial_count += bigint(1)
        else:
            self.failed_evidence_count += bigint(1)

    @gl.public.view
    def get_proposal(self, proposal_id: str) -> str:
        """Retrieve full details of a specific proposal as JSON."""
        if proposal_id not in self.proposals:
            raise gl.UserError("Proposal not found.")
        p = self.proposals[proposal_id]
        return json.dumps({
            "proposal_id": p.proposal_id,
            "submitter": _addr_str(p.submitter),
            "proposal_url": p.proposal_url,
            "title": p.title,
            "status": p.status,
            "risk_score": int(p.risk_score),
            "sentiment": p.sentiment,
            "summary_report": p.summary_report,
            "created_at": str(p.created_at),
            "resolved_at": str(p.resolved_at)
        })

    @gl.public.view
    def get_proposal_count(self) -> int:
        """Return total number of submitted proposals."""
        return int(self.proposal_count)

    @gl.public.view
    def get_owner(self) -> str:
        """Return contract owner address."""
        return _addr_str(self.owner)

    @gl.public.view
    def get_stats(self) -> str:
        """Return high-level statistics across all evaluated DAO proposals."""
        return json.dumps({
            "total_proposals": int(self.proposal_count),
            "analyzed_count": int(self.analyzed_count),
            "high_risk_count": int(self.high_risk_count),
            "favorable_count": int(self.favorable_count),
            "controversial_count": int(self.controversial_count),
            "failed_evidence_count": int(self.failed_evidence_count)
        })

    @gl.public.view
    def get_proposals_page(self, offset: int, limit: int) -> str:
        """Return paginated list of proposals for UI display and analytics."""
        total = int(self.proposal_count)
        if offset < 0:
            offset = 0
        if limit <= 0 or limit > 50:
            limit = 10

        items = []
        for i in range(offset + 1, min(total + 1, offset + limit + 1)):
            pid = str(i)
            if pid in self.proposals:
                p = self.proposals[pid]
                items.append({
                    "proposal_id": p.proposal_id,
                    "submitter": _addr_str(p.submitter),
                    "title": p.title,
                    "proposal_url": p.proposal_url,
                    "status": p.status,
                    "risk_score": int(p.risk_score),
                    "sentiment": p.sentiment,
                    "summary_report": p.summary_report,
                    "created_at": str(p.created_at),
                    "resolved_at": str(p.resolved_at)
                })

        return json.dumps({
            "total": total,
            "offset": offset,
            "limit": limit,
            "items": items
        })
