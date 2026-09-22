# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *
from dataclasses import dataclass
import json


ALLOWED = ("AFFIRMED", "DENIED", "UNBOUND")


@allow_storage
@dataclass
class Case:
    clerk: Address
    question: str
    rubric: str
    url: str
    excerpt: str
    status: str
    justification: str
    round_no: u32


class ExcerptGate(gl.Contract):
    cases: TreeMap[str, Case]
    next_id: u32

    def __init__(self):
        self.next_id = u32(1)

    @gl.public.write
    def bind(self, question: str, rubric: str, url: str, excerpt: str) -> None:
        q = question.strip()
        r = rubric.strip()
        u = url.strip()
        e = excerpt.strip()
        if not q or not r or not u or not e:
            raise Exception("question, rubric, url, excerpt required")
        if len(e) < 12:
            raise Exception("excerpt too short")
        cid = int(self.next_id)
        self.next_id = u32(cid + 1)
        self.cases[str(cid)] = Case(
            clerk=gl.message.sender_address,
            question=q,
            rubric=r,
            url=u,
            excerpt=e[:400],
            status="BOUND",
            justification="",
            round_no=u32(0),
        )

    @gl.public.write
    def adjudicate(self, case_id: str) -> None:
        rec_mem = gl.storage.copy_to_memory(self.cases[case_id])
        if rec_mem.status in ALLOWED:
            raise Exception("already final")
        url = rec_mem.url
        excerpt = rec_mem.excerpt
        question = rec_mem.question
        rubric = rec_mem.rubric

        def collect() -> str:
            try:
                page = gl.nondet.web.render(url, mode="text")
                return "URL: " + url + "\nEXCERPT: " + excerpt + "\nPAGE:\n" + page[:7000]
            except Exception as err:
                return "URL: " + url + "\nEXCERPT: " + excerpt + "\nFAIL: " + str(err)

        raw = gl.eq_principle.prompt_non_comparative(
            collect,
            task=(
                "QUESTION: " + question
                + " RUBRIC: " + rubric
                + " First decide if EXCERPT appears on PAGE."
                + " If fetch failed or excerpt is absent, status UNBOUND."
                + " If excerpt is present and answers yes, AFFIRMED."
                + " If excerpt is present and answers no, DENIED."
                + " Return ONLY JSON keys status, justification."
            ),
            criteria=(
                "JSON with status and justification. "
                + "status exactly AFFIRMED, DENIED or UNBOUND. "
                + "UNBOUND if page missing or excerpt not on the page. "
                + "Do not treat a made-up excerpt as present. "
                + "Valid JSON alone is not enough."
            ),
        )

        if isinstance(raw, dict):
            parsed = raw
        else:
            text = str(raw)
            start = text.find("{")
            end = text.rfind("}")
            try:
                parsed = json.loads(text[start:end + 1]) if start >= 0 and end > start else {}
            except Exception:
                parsed = {"status": "UNBOUND", "justification": "unparseable"}

        status = str(parsed.get("status", "UNBOUND")).upper()
        if status not in ALLOWED:
            status = "UNBOUND"

        rec = self.cases[case_id]
        rec.status = status
        rec.justification = str(parsed.get("justification", ""))[:500]
        rec.round_no = u32(int(rec.round_no) + 1)
        self.cases[case_id] = rec

    @gl.public.write
    def challenge(self, case_id: str, reason: str) -> None:
        rec = self.cases[case_id]
        if rec.clerk != gl.message.sender_address:
            raise Exception("only clerk can challenge")
        if rec.status not in ALLOWED:
            raise Exception("nothing to challenge")
        if not reason.strip():
            raise Exception("reason required")
        rec.status = "CHALLENGED"
        rec.justification = reason.strip()[:500]
        self.cases[case_id] = rec

    @gl.public.view
    def get_case(self, case_id: str) -> str:
        if case_id not in self.cases:
            return "{}"
        rec = self.cases[case_id]
        return json.dumps(
            {
                "clerk": str(rec.clerk),
                "question": rec.question,
                "rubric": rec.rubric,
                "url": rec.url,
                "excerpt": rec.excerpt,
                "status": rec.status,
                "justification": rec.justification,
                "round_no": int(rec.round_no),
            }
        )

    @gl.public.view
    def get_status(self, case_id: str) -> str:
        if case_id not in self.cases:
            return ""
        return self.cases[case_id].status