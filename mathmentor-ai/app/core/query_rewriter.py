"""Retrieval query rewriting with LaTeX preservation."""

from app.core.intent_detector import QueryIntent


class QueryRewriter:
    """Create retrieval variants without modifying mathematical expressions."""

    TOPIC_EXPANSIONS: dict[str, str] = {
        "quadratic_equations": "quadratic equation discriminant delta factoring roots",
        "linear_equations": "linear equation solve isolate variable",
        "trigonometry": "trigonometry sine cosine tangent identities",
        "derivatives": "derivative differentiation slope tangent",
        "integrals": "integral antiderivative area under curve",
        "vectors": "vectors dot product magnitude direction",
        "geometry": "geometry theorem proof diagram",
    }

    async def rewrite(self, query: str, intent: QueryIntent) -> list[str]:
        """Return original query plus retrieval-oriented variants."""
        variants = [query]
        expansions = [
            self.TOPIC_EXPANSIONS[topic]
            for topic in intent.topic_tags
            if topic in self.TOPIC_EXPANSIONS
        ]
        if expansions:
            variants.append(f"{query}\nKeywords: {'; '.join(expansions)}")
        if intent.math_entities:
            variants.append(f"{' '.join(intent.math_entities)} {' '.join(intent.topic_tags)}")
        elif intent.topic_tags:
            variants.append(" ".join(intent.topic_tags))
        return list(dict.fromkeys(variant for variant in variants if variant.strip()))[:3]
