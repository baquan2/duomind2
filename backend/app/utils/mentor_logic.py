import re
from typing import Any

from app.models.mentor import MentorIntent
from app.utils.helpers import build_core_title, normalize_text, normalize_topic_phrase, strip_accents


INTENT_PATTERNS: list[tuple[MentorIntent, tuple[str, ...]]] = [
    ("career_roles", ("vi tri", "vai tro", "nghe", "cong viec", "role", "chuc danh")),
    (
        "market_outlook",
        ("co hoi", "trien vong", "phat trien", "thu nhap", "nhu cau", "thi truong", "jd", "tuyen dung", "yeu cau thi truong"),
    ),
    (
        "skill_gap",
        ("thieu ky nang", "thieu gi", "ky nang can", "kien thuc nao toi can co", "can co gi", "gap", "hong ky nang"),
    ),
    (
        "learning_roadmap",
        ("lo trinh", "nen hoc gi", "hoc gi truoc", "bat dau tu dau", "roadmap", "thu tu hoc", "hoc theo buoc"),
    ),
    ("career_fit", ("phu hop", "hop voi toi", "nen chon huong nao", "nen theo huong nao")),
]

TRACK_KEYWORDS = {
    "dev": "dev",
    "developer": "dev",
    "lap trinh": "dev",
    "frontend": "dev",
    "backend": "dev",
    "fullstack": "dev",
    "web": "dev",
    "mobile": "dev",
    "software": "dev",
    "data analyst": "data",
    "business analyst": "business",
    "business analysis": "business",
    "requirement": "business",
    "user story": "business",
    "stakeholder": "business",
    "process mapping": "business",
    "nghiep vu": "business",
    "phan tich du lieu": "data",
    "sql": "data",
    "power bi": "data",
    "tableau": "data",
    "marketing": "marketing",
    "digital marketing": "marketing",
    "content": "marketing",
    "seo": "marketing",
    "product": "product",
    "product manager": "product",
}

GENERIC_MARKERS = (
    "minh chua co phan hoi day du",
    "minh chua co du du lieu",
    "mentor chua gom du du lieu",
    "theo huong an toan",
    "neu ban hoi cu the hon",
    "minh da hieu cau hoi cua ban",
    "minh da ghi nhan muc tieu",
    "hay neu ro 3 diem",
    "hay cho toi them",
)

SKILL_CATALOG = {
    "dev": ["JavaScript", "TypeScript", "HTML/CSS", "Git/GitHub", "API/HTTP", "SQL", "React", "Node.js"],
    "data": ["Excel", "SQL", "Python", "Power BI", "Tableau", "Statistics", "Dashboarding"],
    "business": [
        "Requirement analysis",
        "User story",
        "Process mapping",
        "Stakeholder communication",
        "Use case",
        "Acceptance criteria",
    ],
    "marketing": ["Customer insight", "Content", "SEO", "Meta Ads", "Google Ads", "Google Analytics"],
    "product": ["User research", "Roadmapping", "Product metrics", "SQL", "A/B testing"],
    "general": ["Problem solving", "Communication", "Project work", "Portfolio"],
}

FORBIDDEN_GENERIC_PHRASES = (
    "con tuy",
    "ban co the can nhac",
    "hay cho them thong tin",
    "minh chua co du du lieu",
    "theo huong an toan",
)

MENTOR_TOPIC_STOPWORDS = {
    "la",
    "gi",
    "ve",
    "va",
    "voi",
    "nhu",
    "the",
    "nao",
    "tai",
    "sao",
    "khi",
    "can",
    "nen",
    "hoc",
    "giup",
    "cho",
    "mot",
    "nhung",
    "cua",
    "toi",
    "minh",
    "em",
    "ban",
    "hay",
}

KNOWLEDGE_QUESTION_MARKERS = (
    "la gi",
    "la nhu the nao",
    "gom gi",
    "gom nhung gi",
    "thanh phan",
    "cau truc",
    "khac nhau",
    "khac gi",
    "o diem nao",
    "phan biet",
    "so sanh",
    "giai thich",
    "ban chat",
    "co che",
    "hoat dong",
    "van hanh",
    "tai sao",
    "khi nao dung",
    "truong hop nao dung",
    "vi du",
)

PERSONAL_GUIDANCE_MARKERS = (
    "toi nen",
    "minh nen",
    "em nen",
    "phu hop voi toi",
    "hop voi toi",
    "cho toi",
    "lo trinh",
    "roadmap",
    "thieu ky nang",
    "skill gap",
    "thi truong",
    "jd",
    "tuyen dung",
    "thu nhap",
    "co hoi viec lam",
    "muc tieu cua toi",
    "ho so cua toi",
)

PROFILE_LOOKUP_MARKERS = (
    "theo ho so cua toi",
    "theo ho so cua minh",
    "theo profile cua minh",
    "theo profile cua toi",
    "dua tren ho so cua toi",
    "dua tren ho so cua minh",
    "dua vao ho so cua toi",
    "dua vao ho so cua minh",
    "trong ho so cua toi",
    "trong ho so cua minh",
    "trong profile cua toi",
    "trong profile cua minh",
    "ho so cua toi",
    "ho so cua minh",
    "ho so em",
    "profile cua toi",
    "profile cua minh",
    "profile em",
    "toi dang hoc nganh nao",
    "toi hoc truong nao",
    "toi dang theo huong gi",
    "toi dang theo huong nao",
    "toi dang hoc nganh gi",
    "ho so hien tai cua toi",
)

PROFILE_DENIAL_MARKERS = (
    "khong the xac dinh",
    "khong the truy cap",
    "khong co kha nang truy cap",
    "khong co ho so cua ban",
    "khong co profile cua ban",
    "khong luu tru thong tin ca nhan",
)

INTENT_RESPONSE_POLICIES: dict[MentorIntent, dict[str, Any]] = {
    "career_roles": {
        "primary_goal": "De xuat toi da 3 vai tro va chot 1 vai tro uu tien nhat.",
        "must_include": [
            "fit_reason bam profile",
            "entry_level",
            "2-4 ky nang cot loi",
            "1 buoc tiep theo trong 7 ngay",
        ],
        "avoid": ["roadmap qua dai", "qua 3 lua chon ngang nhau"],
    },
    "market_outlook": {
        "primary_goal": "Ket luan co hoi thi truong truoc, sau do moi neu tac dong den viec hoc.",
        "must_include": [
            "ket luan ngan ve nhu cau thi truong",
            "2-4 ky nang duoc nhac nhieu",
            "1 hanh dong de kiem chung hoac bat dau",
        ],
        "avoid": ["bien thanh roadmap dai", "ly thuyet chung chung"],
    },
    "skill_gap": {
        "primary_goal": "Chi ra 3 ky nang thieu quan trong nhat va thu tu bu truoc.",
        "must_include": [
            "3 skill gaps toi da",
            "ly do bam target_role/desire/challenge",
            "3 hanh dong cu the",
        ],
        "avoid": ["ban qua sau ve thi truong", "nhieu lua chon ngang nhau"],
    },
    "learning_roadmap": {
        "primary_goal": "Dua 3 buoc roadmap theo thu tu va moi buoc co dau ra cu the.",
        "must_include": [
            "thu tu hoc",
            "output moi buoc",
            "ke hoach trong 7 ngay tiep theo",
        ],
        "avoid": ["list kien thuc dai dong", "roadmap khong co output"],
    },
    "career_fit": {
        "primary_goal": "Chot 1 huong phu hop nhat truoc, chi neu them 1-2 huong phu.",
        "must_include": [
            "1 huong uu tien",
            "ly do bam profile",
            "1 buoc tiep theo de kiem chung su phu hop",
        ],
        "avoid": ["so sanh lan man", "3+ lua chon dong hang"],
    },
    "general_guidance": {
        "primary_goal": "Tra loi truc dien dung cau hoi hien tai; chi dua hanh dong khi cau hoi thuc su can.",
        "must_include": [
            "cau tra loi cot loi",
            "giai thich du de hieu",
            "vi du, phan biet, hoac luu y khi can",
        ],
        "avoid": ["coaching ep buoc", "cau tra loi an toan", "van phong rong thong tin"],
    },
}

MAX_ANSWER_WORDS = 220
MAX_STEP_WORDS = 26
MAX_FOLLOWUP_WORDS = 18


def mentor_compare_subjects(message: str) -> tuple[str, str] | None:
    normalized = normalize_text(message)
    patterns = [
        r"(.+?)\s+(?:khac)\s+(.+?)\s+(?:o)\s+(?:diem)\s+nao\??$",
        r"so sanh\s+(.+?)\s+va\s+(.+?)$",
        r"phan biet\s+(.+?)\s+va\s+(.+?)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, normalized, flags=re.IGNORECASE)
        if not match:
            continue
        first = normalize_text(match.group(1).strip(" ?"))
        second = normalize_text(match.group(2).strip(" ?"))
        if first and second:
            return first, second
    return None


def mentor_question_type(message: str) -> str:
    lowered = strip_accents(normalize_text(message)).lower()
    if mentor_compare_subjects(message):
        return "comparison"
    if any(
        marker in lowered
        for marker in ("la gi", "dinh nghia", "khai niem", "ban chat", "gom gi", "gom nhung gi", "thanh phan", "cau truc")
    ):
        return "definition"
    if any(marker in lowered for marker in ("co che", "hoat dong", "van hanh", "tai sao", "nhu the nao")):
        return "mechanism"
    return "general"


def question_focus_terms(message: str) -> list[str]:
    normalized = strip_accents(normalize_text(message)).lower()
    tokens = re.findall(r"[0-9a-z]+", normalized)
    focus_terms: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        if len(token) < 3 or token in MENTOR_TOPIC_STOPWORDS or token.isdigit():
            continue
        if token in seen:
            continue
        seen.add(token)
        focus_terms.append(token)
        if len(focus_terms) >= 8:
            break
    return focus_terms


def looks_like_direct_knowledge_question(message: str) -> bool:
    lowered = strip_accents(normalize_text(message)).lower()
    if not lowered:
        return False
    has_knowledge_marker = any(marker in lowered for marker in KNOWLEDGE_QUESTION_MARKERS)
    if not has_knowledge_marker:
        return False
    if any(marker in lowered for marker in PERSONAL_GUIDANCE_MARKERS):
        return False
    personal_pronoun_hits = sum(1 for marker in (" toi ", " minh ", " em ") if marker in f" {lowered} ")
    return personal_pronoun_hits <= 1


def is_profile_lookup_question(message: str) -> bool:
    lowered = strip_accents(normalize_text(message)).lower()
    if not lowered:
        return False
    return any(marker in lowered for marker in PROFILE_LOOKUP_MARKERS)


def profile_lookup_requested_fields(message: str) -> list[str]:
    lowered = strip_accents(normalize_text(message)).lower()
    requested: list[str] = []

    def add(field: str) -> None:
        if field not in requested:
            requested.append(field)

    if any(marker in lowered for marker in ("huong gi", "huong nao", "dinh huong", "target role", "muc tieu nghe nghiep")):
        add("direction")
    if any(marker in lowered for marker in ("nganh nao", "hoc nganh nao", "major", "chuyen nganh")):
        add("major")
    if any(marker in lowered for marker in ("truong nao", "hoc truong nao", "school", "ten truong")):
        add("school_name")
    if any(marker in lowered for marker in ("trang thai", "dang la sinh vien", "dang di lam", "vua hoc vua lam")):
        add("status")
    if any(marker in lowered for marker in ("vai tro hien tai", "job title", "cong viec hien tai")):
        add("job_title")
    if any(marker in lowered for marker in ("nganh nghe", "industry", "linh vuc hien tai")):
        add("industry")
    if not requested and is_profile_lookup_question(message):
        return ["direction", "major", "school_name"]
    return requested


def answer_denies_profile_access(answer: str) -> bool:
    lowered = strip_accents(normalize_text(answer)).lower()
    if not lowered:
        return False
    return any(marker in lowered for marker in PROFILE_DENIAL_MARKERS)


def general_guidance_requirements(message: str) -> tuple[str, str, list[str]]:
    question_type = mentor_question_type(message)
    if question_type == "comparison":
        return (
            "Tra loi truc dien bang cach phan biet dung trong tam cau hoi hien tai.",
            "direct comparison answer",
            [
                "diem giong hoac diem khac cot loi",
                "2-3 truc so sanh ro rang",
                "khi nao de nham hoac dung sai",
            ],
        )
    if question_type == "definition":
        return (
            "Giai thich dung khai niem va pham vi cua chu de dang duoc hoi.",
            "focused concept explanation",
            [
                "dinh nghia cot loi",
                "ranh gioi hoac dieu khong nen nham",
                "vi du hoac gioi han ap dung",
            ],
        )
    if question_type == "mechanism":
        return (
            "Giai thich chu de van hanh ra sao va vi sao no tao ra ket qua nhu vay.",
            "mechanism explanation",
            [
                "co che hoac logic van hanh",
                "luong dau vao -> xu ly -> dau ra hoac quan he nhan qua",
                "vi du hoac dieu kien ap dung",
            ],
        )
    return (
        "Tra loi truc dien dung cau hoi hien tai cua nguoi dung.",
        "direct answer",
        [
            "cau tra loi cot loi",
            "giai thich du de hieu",
            "vi du, phan biet, hoac luu y khi can",
        ],
    )


def detect_mentor_intent(message: str) -> MentorIntent:
    text = strip_accents(normalize_text(message)).lower()
    if looks_like_direct_knowledge_question(message):
        return "general_guidance"

    scores: dict[MentorIntent, int] = {
        "career_roles": 0,
        "market_outlook": 0,
        "skill_gap": 0,
        "learning_roadmap": 0,
        "career_fit": 0,
        "general_guidance": 0,
    }
    for intent, keywords in INTENT_PATTERNS:
        for keyword in keywords:
            if strip_accents(keyword).lower() in text:
                scores[intent] += 1

    if "roadmap" in text or "lo trinh" in text:
        scores["learning_roadmap"] += 2
    if "thi truong" in text or "tuyen dung" in text or "jd" in text:
        scores["market_outlook"] += 2
    if "thieu ky nang" in text or "skill gap" in text:
        scores["skill_gap"] += 2
    if any(marker in text for marker in PERSONAL_GUIDANCE_MARKERS):
        scores["general_guidance"] -= 1

    strongest_intent = max(scores.items(), key=lambda item: item[1])
    if strongest_intent[1] > 0:
        return strongest_intent[0]
    return "general_guidance"


def mentor_focus_topic(message: str) -> str:
    compare_subjects = mentor_compare_subjects(message)
    if compare_subjects:
        return normalize_text(f"{compare_subjects[0]} va {compare_subjects[1]}")

    normalized_topic = normalize_topic_phrase(message) or normalize_text(message).strip(" ?")
    compact = build_core_title(normalized_topic, "")
    return compact or normalized_topic or "chu de hien tai"


def should_use_profile_context(intent: MentorIntent, message: str) -> bool:
    if intent != "general_guidance":
        return True
    lowered = strip_accents(normalize_text(message)).lower()
    return any(marker in lowered for marker in PERSONAL_GUIDANCE_MARKERS)


def should_use_market_context(intent: MentorIntent) -> bool:
    return intent in {"career_roles", "market_outlook", "skill_gap", "learning_roadmap", "career_fit"}


def build_general_guidance_followups(
    message: str,
    focus_topic: str,
    compare_subjects: tuple[str, str] | None,
) -> list[str]:
    question_type = mentor_question_type(message)
    if compare_subjects:
        first, second = compare_subjects
        return [
            f"Khi nao de nham giua {first} va {second} trong thuc te?",
            f"Neu dat {first} va {second} trong cung mot bai toan, dau ra cua moi ben khac nhau o dau?",
            f"Co khai niem nao gan voi {first} va {second} nhung de bi dong nhat sai khong?",
        ]

    if question_type == "definition":
        return [
            f"Co che van hanh cua {focus_topic} nhin theo dau vao -> xu ly -> dau ra ra sao?",
            f"{focus_topic} de bi nham voi khai niem nao gan giong?",
            f"Khi nao nen dung va khi nao khong nen dung {focus_topic}?",
        ]
    if question_type == "mechanism":
        return [
            f"Dieu kien nao lam cho co che cua {focus_topic} phat huy tac dung hoac mat tac dung?",
            f"Neu doi dau vao cua {focus_topic}, dau ra se thay doi nhu the nao?",
            f"Hieu lam pho bien nao khien nguoi hoc de dung sai {focus_topic}?",
        ]
    return [
        f"Cho mot vi du sat thuc te de thay {focus_topic} van hanh ra sao.",
        f"Ranh gioi ap dung cua {focus_topic} nam o dau?",
        f"Khai niem nao nen hoc tiep ngay sau {focus_topic} de hieu sau hon?",
    ]


def general_guidance_answer_matches_question(answer: str, message: str) -> bool:
    normalized_answer = strip_accents(normalize_text(answer)).lower()
    if not normalized_answer:
        return False

    compare_subjects = mentor_compare_subjects(message)
    if compare_subjects:
        lowered_answer = f" {normalized_answer} "
        return all(strip_accents(subject).lower() in lowered_answer for subject in compare_subjects) and any(
            marker in lowered_answer for marker in (" khac ", " phan biet ", " trong khi ", " con ")
        )

    question_type = mentor_question_type(message)
    focus_topic = strip_accents(mentor_focus_topic(message)).lower()
    focus_terms = question_focus_terms(message)
    if not focus_terms:
        return len(normalized_answer.split()) >= 24

    hits = sum(1 for term in focus_terms[:5] if term in normalized_answer)
    if question_type == "definition":
        return (
            hits >= 1
            and focus_topic in normalized_answer
            and any(marker in f" {normalized_answer} " for marker in (" la ", " la mot ", " duoc dung de ", " ban chat "))
        )
    if question_type == "mechanism":
        return hits >= 1 and any(
            marker in normalized_answer
            for marker in ("co che", "dau vao", "xu ly", "dau ra", "van hanh", "nguyen nhan", "he qua")
        )
    return hits >= max(2, min(3, len(focus_terms[:5])))


__all__ = [
    "FORBIDDEN_GENERIC_PHRASES",
    "GENERIC_MARKERS",
    "INTENT_RESPONSE_POLICIES",
    "MAX_ANSWER_WORDS",
    "MAX_FOLLOWUP_WORDS",
    "MAX_STEP_WORDS",
    "SKILL_CATALOG",
    "TRACK_KEYWORDS",
    "build_general_guidance_followups",
    "detect_mentor_intent",
    "general_guidance_answer_matches_question",
    "general_guidance_requirements",
    "is_profile_lookup_question",
    "profile_lookup_requested_fields",
    "answer_denies_profile_access",
    "looks_like_direct_knowledge_question",
    "mentor_compare_subjects",
    "mentor_focus_topic",
    "mentor_question_type",
    "question_focus_terms",
    "should_use_market_context",
    "should_use_profile_context",
]
