from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from jinja2 import Environment, StrictUndefined, TemplateSyntaxError, UndefinedError, Undefined


class TemplateRenderError(ValueError):
    """Raised when Jinja template rendering fails."""
    pass


class DirectiveUndefined(Undefined):
    """
    Custom undefined handler that treats undefined names as directive functions.

    This allows custom directives (not in the global registry) to still be parsed.
    Variables that are accessed but not called as functions will still raise errors.
    """
    def __call__(self, *args, **kwargs):
        # When an undefined name is called as a function, treat it as a directive
        return DirectiveFunction(self._undefined_name)(*args, **kwargs)

    def __str__(self):
        # When undefined variable is rendered as string, raise error
        self._fail_with_undefined_error()

    def __getattr__(self, name):
        if name.startswith('_'):
            raise AttributeError(name)
        # Return another undefined for chained access
        return self

    def __int__(self):
        self._fail_with_undefined_error()

    def __float__(self):
        self._fail_with_undefined_error()

    def __bool__(self):
        self._fail_with_undefined_error()


@dataclass(frozen=True)
class DirectiveMarker:
    """Marker object returned by directive functions during template parsing."""
    name: str
    args: tuple[Any, ...]
    kwargs: dict[str, Any]
    raw_text: str
    placeholder: str


# Global list to collect markers during rendering
_marker_collector: list[DirectiveMarker] = []


class DirectiveFunction:
    """Jinja-compatible directive function that collects markers."""

    def __init__(self, name: str):
        self.name = name

    def __call__(self, *args, **kwargs) -> str:
        """Called by Jinja during template rendering."""
        # Create unique placeholder
        marker_id = f"__DIRECTIVE_{len(_marker_collector)}__"

        # Reconstruct the call syntax
        args_str = ", ".join(repr(arg) for arg in args)
        kwargs_str = ", ".join(f"{k}={v!r}" for k, v in kwargs.items())
        all_args = ", ".join(filter(None, [args_str, kwargs_str]))
        raw_text = f"{{{{ {self.name}({all_args}) }}}}"

        # Create marker
        marker = DirectiveMarker(
            name=self.name,
            args=args,
            kwargs=kwargs,
            raw_text=raw_text,
            placeholder=marker_id
        )
        _marker_collector.append(marker)

        # Return placeholder that will be in rendered output
        return marker_id


def render_template(
    source: str,
    variables: dict[str, str] | None = None
) -> tuple[str, list[DirectiveMarker]]:
    """
    Render SQL source with Jinja2, extracting directives and variables.

    Uses {{ }} syntax for both variables and directive functions.

    Args:
        source: Raw SQL file content with Jinja template syntax
        variables: Dictionary of variable name -> value mappings

    Returns:
        Tuple of (rendered_source_with_placeholders, directive_markers)

    Raises:
        TemplateRenderError: If rendering fails
    """
    global _marker_collector
    _marker_collector = []  # Reset collector

    env = Environment(
        undefined=DirectiveUndefined,
        autoescape=False,
        finalize=lambda x: '' if x is None else x
    )

    # Register directive functions as Jinja globals
    env.globals['success'] = DirectiveFunction('success')
    env.globals['fail'] = DirectiveFunction('fail')
    env.globals['assess'] = DirectiveFunction('assess')

    template_vars = variables or {}

    try:
        template = env.from_string(source)
        rendered = template.render(**template_vars)
    except UndefinedError as exc:
        raise TemplateRenderError(f"Undefined variable in template: {exc}") from exc
    except TemplateSyntaxError as exc:
        raise TemplateRenderError(f"Template syntax error: {exc}") from exc
    except Exception as exc:
        raise TemplateRenderError(f"Failed to render template: {exc}") from exc

    # Collect markers and clear global list
    markers = list(_marker_collector)
    _marker_collector = []

    return rendered, markers
