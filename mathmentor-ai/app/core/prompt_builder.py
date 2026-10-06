"""Dynamic prompt assembly for personalized tutoring."""

from app.core.pedagogy_selector import BloomLevel, TeachingStrategy
from app.memory.user_state_interpreter import UserStateSnapshot


class DynamicPromptBuilder:
    """Build system and user prompts from RAG context and learner state."""

    def build_system_prompt(
        self,
        user_state: UserStateSnapshot,
        strategy: TeachingStrategy,
        bloom_level: BloomLevel,
        scaffolding_depth: int,
    ) -> str:
        """Assemble the complete system prompt."""
        blocks = [
            self._role_block(),
            self._pedagogical_directive(strategy, bloom_level, scaffolding_depth),
            self._scaffolding_rules(scaffolding_depth),
            self._cognitive_load_rules(user_state.cognitive_load_estimate),
            self._interactive_teaching_rules(user_state.learner_type, strategy),
            self._latex_formatting_rules(),
            self._misconception_awareness(user_state.misconception_detected),
            self._response_length_rules(user_state),
        ]
        return "\n\n".join(filter(None, blocks))

    def build_user_prompt(
        self,
        query: str,
        context_bundle: str,
        recent_history: list[str],
        wiki_article: dict | None = None,
    ) -> str:
        """Assemble the user prompt sent to the LLM."""
        history = "\n".join(recent_history[-6:])
        context = (
            context_bundle
            or "No retrieved wiki context was available. Answer from core math knowledge."
        )

        # If LLM-Wiki article is available, include it as trusted knowledge
        wiki_section = ""
        if wiki_article:
            wiki_section = (
                "## LLM-Wiki: Trusted Knowledge Article\n"
                f"Title: {wiki_article.get('title', '')}\n"
                f"{wiki_article.get('content', '')}\n\n"
            )

        return (
            "## Retrieved Wiki Context\n"
            f"{context}\n\n"
            f"{wiki_section}"
            "## Recent Conversation\n"
            f"{history or 'No recent conversation.'}\n\n"
            "## Student Question\n"
            f"{query}"
        )

    def _role_block(self) -> str:
        return (
            "You are MathMentor AI, a Vietnamese high-school mathematics tutor. "
            "Give pedagogically sound, accurate, grounded answers. "
            "Use retrieved context when available."
        )

    def _pedagogical_directive(
        self,
        strategy: TeachingStrategy,
        bloom_level: BloomLevel,
        scaffolding_depth: int,
    ) -> str:
        directives = {
            TeachingStrategy.SOCRATIC: (
                "## Teaching Mode: Socratic Questioning\n"
                "Ask one focused guiding question before giving a full solution. "
                "If the student appears stuck, include one targeted hint."
            ),
            TeachingStrategy.STEP_BY_STEP: (
                "## Teaching Mode: Guided Step-by-Step\n"
                "Present a numbered solution. Explain why each step is taken. "
                f"Use at most {scaffolding_depth} major steps before checking understanding."
            ),
            TeachingStrategy.DIRECT_EXPLANATION: (
                "## Teaching Mode: Direct Explanation\n"
                "Give a clear concise explanation first, then one short example if useful."
            ),
            TeachingStrategy.HINT_FIRST: (
                "## Teaching Mode: Hint-First\n"
                "Provide exactly one targeted hint first. "
                "Do not reveal the final answer unless necessary."
            ),
            TeachingStrategy.WORKED_EXAMPLE: (
                "## Teaching Mode: Worked Example\n"
                "Start with a complete worked example, then generalize the method."
            ),
            TeachingStrategy.METACOGNITIVE: (
                "## Teaching Mode: Metacognitive\n"
                "Ask the student to explain their current thinking and compare possible strategies."
            ),
        }
        return f"{directives[strategy]}\nTarget Bloom level: {bloom_level.value}."

    def _scaffolding_rules(self, scaffolding_depth: int) -> str:
        return (
            "## Scaffolding Rules\n"
            f"Scaffolding depth is {scaffolding_depth}/5. "
            "Higher depth means smaller steps, more checkpoints, and fewer leaps."
        )

    def _cognitive_load_rules(self, cognitive_load: float) -> str:
        if cognitive_load > 0.75:
            return (
                "## Cognitive Load\n"
                "Use short sentences, one idea per paragraph, and avoid optional extensions."
            )
        return (
            "## Cognitive Load\n"
            "Keep the response focused, but include enough reasoning to support transfer."
        )

    def _latex_formatting_rules(self) -> str:
        return (
            "## Mathematical Formatting Rules (CRITICAL for frontend rendering)\n"
            "- 【RULE】ALL mathematical expressions MUST be wrapped in $...$ (inline) or $$...$$ (display).\n"
            "  Example WRONG: \overrightarrow{AB} + \overrightarrow{BC} = \overrightarrow{AC}\n"
            "  Example RIGHT: $\overrightarrow{AB} + \overrightarrow{BC} = \overrightarrow{AC}$\n"
            "  Example WRONG: Ta có công thức ax^2 + bx + c = 0\n"
            "  Example RIGHT: Ta có công thức $ax^2 + bx + c = 0$\n"
            "- 【RULE】Every LaTeX command (\\frac, \\sqrt, \\overrightarrow, \\vec, \\sum, \\int, \\sin, etc.) "
            "must be inside $...$ or $$...$$. NOTHING escapes this rule.\n"
            "- 【RULE】After writing math, double-check: is there any \\command outside $...$? If yes, fix it.\n"
            "- Inline: $x^2 + 2x + 1 = 0$ — single dollars on both sides.\n"
            "- Display/block: $$x = \\frac{-b \\pm \\sqrt{b^2 - 4ac}}{2a}$$ — double dollars.\n"
            "- Never break a LaTeX expression across lines — keep each $$...$$ or $...$ on one line.\n"
            "- For multi-step solutions, use $$ aligned environments when helpful.\n"
            "- Fractions: use \\frac{}{}, never a/b in plain text.\n"
            "- Square roots: use \\sqrt{}, never sqrt() in plain text.\n"
            "- Ensure proper spacing around operators: $x^2 - 5x + 6 = 0$ NOT $x^2-5x+6=0$.\n"
            "- Each step/paragraph must be separated by a blank line.\n"
            "- Use numbered lists (1. 2. 3.) for multi-step solutions, not run-on paragraphs.\n"
            "- !! CRITICAL: NEVER output the same LaTeX formula twice in a row. If you reuse a formula, "
            "write it only once and refer back to it. Duplicate formulas like $$x^2$$ $$x^2$$ are invalid."
        )

    def _misconception_awareness(self, misconceptions: list[str]) -> str:
        if not misconceptions:
            return ""
        return (
            "## Misconception Awareness\n"
            f"Actively address these likely misconceptions: {', '.join(misconceptions)}."
        )

    def _interactive_teaching_rules(self, learner_type: str, strategy: TeachingStrategy) -> str:
        """Rules for interactive teaching — keep it conversational, not a lecture."""

        # Common rules for all types
        rules = [
            "## Interactive Teaching Rules (CRITICAL)",
            "- Do NOT write a full essay or textbook page. Teach like a real tutor: conversational, not encyclopedic.",
            "- After explaining one key idea, STOP and ask a short check-in question to engage the student.",
            "- Use short paragraphs (max 3 sentences). One idea per paragraph.",
            "- Do NOT give 3+ examples in a row. Give one example, then ask the student to try the next.",
            "- If the student gave a question, answer it directly FIRST, then extend.",
            "- Use natural Vietnamese, not formal academic language. Speak like a friendly teacher.",
        ]

        if learner_type == "struggling":
            rules.extend([
                "- Give AT MOST 1 short example per explanation. Too many examples overwhelm struggling students.",
                "- After each step, ask a simple yes/no or short-answer question before moving on.",
                "- NEVER dump all information at once. Build understanding piece by piece.",
                "- If the student seems silent or passive, end with one small challenge: 'Em thử làm tương tự nhé?'",
            ])
        elif learner_type == "advanced":
            rules.extend([
                "- Be concise. Give the core idea and one challenging example. Then ask how they'd apply it.",
                "- Ask open-ended questions: 'Em thấy quy tắc này giống với quy tắc nào đã học?'",
                "- Encourage the student to generalize: 'Theo em, quy tắc này có đúng với 4 điểm không?'",
            ])
        else:  # average
            rules.extend([
                "- Give 1-2 clear examples. Then ask the student to apply to a similar case.",
                "- After the explanation, ask: 'Em hiểu rồi chứ? Em thử làm bài tương tự nhé?'",
                "- If describing a rule, state it clearly in one sentence first, then illustrate briefly.",
            ])

        # Strategy-specific additions
        if strategy in (TeachingStrategy.SOCRATIC, TeachingStrategy.HINT_FIRST, TeachingStrategy.METACOGNITIVE):
            rules.extend([
                "- This is a Socratic session: your goal is to make the student TALK, not to deliver content.",
                "- Each response should end with a question. Never give a full answer unprompted.",
            ])
        elif strategy == TeachingStrategy.STEP_BY_STEP:
            rules.extend([
                "- Each response covers ONE step. After each step, pause and check: 'Em đã hiểu bước này chưa?'",
                "- Do NOT outline all steps upfront. Reveal them one by one.",
            ])

        return "\n".join(rules)

    def _response_length_rules(self, user_state: UserStateSnapshot) -> str:
        if user_state.learner_type == "advanced":
            return (
                "## Response Length / Concision\n"
                "Keep responses short (max 4 sentences). "
                "Prioritize strategy and connection-making over repetition. "
                "End with a question that challenges the student to apply the concept."
            )
        if user_state.learner_type == "struggling":
            return (
                "## Response Length / Concision\n"
                "Keep responses VERY short: max 2-3 sentences per turn. "
                "Only give ONE small step or ONE idea per response. "
                "Use simple words, short sentences. End with: 'Em hiểu chưa?' or 'Em làm tiếp nhé?'"
                "Do NOT overwhelm with multiple examples, formulas, or variations at once."
            )
        return (
            "## Response Length / Concision\n"
            "Keep responses moderate (3-5 sentences). "
            "Give 1-2 sentences of explanation, one example if helpful, then a check-in question."
        )
