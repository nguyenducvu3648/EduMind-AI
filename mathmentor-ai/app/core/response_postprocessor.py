"""LLM response validation and safety post-processing."""

import re

from app.utils.latex_utils import LatexValidationError, validate_safe_latex


class ResponsePostprocessor:
    """Validate and lightly normalize tutor responses."""

    def process(self, response: str) -> str:
        """Return a safe markdown response or raise for invalid LaTeX."""
        cleaned = response.strip()
        cleaned = re.sub(r"<script.*?>.*?</script>", "", cleaned, flags=re.IGNORECASE | re.DOTALL)
        try:
            validate_safe_latex(cleaned)
        except LatexValidationError:
            cleaned = self._repair_unbalanced_dollars(cleaned)
            validate_safe_latex(cleaned)
        return cleaned

    def _repair_unbalanced_dollars(self, response: str) -> str:
        if response.count("$$") % 2 != 0:
            response += "$$"
        without_blocks = re.sub(r"\$\$.*?\$\$", "", response, flags=re.DOTALL)
        if without_blocks.count("$") % 2 != 0:
            response += "$"
        return response
