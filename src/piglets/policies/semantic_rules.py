from enum import Enum
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from piglets.utils import read_markdown_file


class RuleMode(str, Enum):
    OFF = "off"
    WARN = "warn"
    STANDARD = "standard"
    STRICT = "strict"
    AGGRESSIVE = "aggressive"


class SemanticRules(BaseModel):
    model_config = ConfigDict(frozen=True)

    joins: RuleMode = RuleMode.STANDARD
    grain: RuleMode = RuleMode.STANDARD
    time: RuleMode = RuleMode.STANDARD
    metrics: RuleMode = RuleMode.STANDARD
    ambiguity: RuleMode = RuleMode.WARN

    def critical_rules_to_string(self) -> str:
        prompts_dir = Path(__file__).resolve().parent / "prompts"
        return read_markdown_file(prompts_dir / "critical_rules.md").strip()

    def to_string(self) -> str:
        sections = [
            self.critical_rules_to_string(),
        ]
        prompts_dir = Path(__file__).resolve().parent / "prompts"

        for domain, mode in (
            ("joins", self.joins),
            ("grain", self.grain),
            ("time", self.time),
            ("metrics", self.metrics),
            ("ambiguity", self.ambiguity),
        ):
            if mode is RuleMode.OFF:
                continue

            prompt_sections = _parse_mode_sections(
                read_markdown_file(prompts_dir / f"{domain}.md")
            )

            if mode is RuleMode.WARN:
                if RuleMode.WARN.value in prompt_sections:
                    sections.append(prompt_sections[RuleMode.WARN.value])
                elif RuleMode.STANDARD.value in prompt_sections:
                    sections.append(prompt_sections[RuleMode.STANDARD.value])
                else:
                    raise ValueError(
                        f"Policy fragment '{domain}' is missing both "
                        "'warn' and 'standard' sections."
                    )
                continue

            required_modes = [RuleMode.STANDARD.value]
            if mode is RuleMode.STRICT:
                required_modes.append(RuleMode.STRICT.value)
            elif mode is RuleMode.AGGRESSIVE:
                required_modes.append(RuleMode.AGGRESSIVE.value)

            for required_mode in required_modes:
                if required_mode not in prompt_sections:
                    raise ValueError(
                        f"Policy fragment '{domain}' is missing the "
                        f"'{required_mode}' section."
                    )
                sections.append(prompt_sections[required_mode])

        return "\n\n".join(section for section in sections if section).strip()


def _parse_mode_sections(markdown_text: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current_mode: str | None = None

    for line in markdown_text.splitlines():
        if line.startswith("# "):
            current_mode = line[2:].strip().lower()
            sections[current_mode] = []
            continue
        if current_mode is not None:
            sections[current_mode].append(line)

    return {
        mode: "\n".join(lines).strip()
        for mode, lines in sections.items()
        if "\n".join(lines).strip()
    }
