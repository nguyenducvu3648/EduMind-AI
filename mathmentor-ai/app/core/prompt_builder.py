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
            "## Mathematical Formatting Rules (MANDATORY)\n"
            "- All inline mathematics must be wrapped in single dollar signs: $x^2 + 2x + 1$\n"
            "- All display/block mathematics must be wrapped in double dollar signs.\n"
            "- Never use plain text for mathematical expressions; wrap them in LaTeX delimiters.\n"
            "- Never break a LaTeX expression across lines.\n"
            "- For multi-step solutions, use aligned environments when helpful."
        )

    def _misconception_awareness(self, misconceptions: list[str]) -> str:
        if not misconceptions:
            return ""
        return (
            "## Misconception Awareness\n"
            f"Actively address these likely misconceptions: {', '.join(misconceptions)}."
        )

    def _response_length_rules(self, user_state: UserStateSnapshot) -> str:
        if user_state.learner_type == "advanced":
            return "## Response Length\nBe concise and emphasize strategy over repetition."
        if user_state.learner_type == "struggling":
            return (
                "## Response Length\nUse a supportive explanation with small steps and checkpoints."
            )
        return "## Response Length\nUse a balanced response."
