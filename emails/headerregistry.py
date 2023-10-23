"""
Extend Python's email.headerregistry for Relay.

The library provides email.headerregistry.HeaderRegistry and several header classes to
parse and generate RFC-compliant email headers. However, Relay needs to be able to
handle emails with non-compliant headers as well.

See:
https://docs.python.org/3/library/email.headerregistry.html
https://github.com/python/cpython/blob/main/Lib/email/headerregistry.py
"""

from email._header_value_parser import get_unstructured, InvalidMessageID
from email.headerregistry import (
    MessageIDHeader as PythonMessageIDHeader,
    HeaderRegistry as PythonHeaderRegistry,
    UnstructuredHeader,
)
from email import errors

from typing import cast, TYPE_CHECKING

if TYPE_CHECKING:
    # _HeaderParser is a protocol from mypy's typeshed
    # https://github.com/python/typeshed/blob/main/stdlib/email/headerregistry.pyi
    from email.headerregistry import _HeaderParser


class RelayMessageIDHeader(PythonMessageIDHeader):
    """
    Handle an IndexError raised by parsing an invalid Message-ID header.

    This issue is tracked in
    https://github.com/python/cpython/issues/105802

    A fix is unmerged as of October 2023:
    https://github.com/python/cpython/pull/108133
    """

    @classmethod
    def parse(cls, value, kwds):
        try:
            parse_tree = cls.value_parser(value)
        except IndexError:
            token = get_unstructured(value)
            message_id = InvalidMessageID(token)
            message_id.defects.append(
                errors.InvalidHeaderDefect(
                    f"IndexError for invalid msg-id in '{value}'"
                )
            )
            parse_tree = message_id
        kwds["parse_tree"] = parse_tree
        kwds["decoded"] = str(parse_tree)
        kwds["defects"].extend(parse_tree.all_defects)


class RelayHeaderRegistry(PythonHeaderRegistry):
    """Extend the HeaderRegistry to store the unstructured header."""

    def __call__(self, name, value):
        """Add the unstructured header as .as_unstructured."""
        header_instance = super().__call__(name, value)
        as_unstructured_cls = type(
            "_UnstructuredHeader", (UnstructuredHeader, self.base_class), {}
        )
        as_unstructured = as_unstructured_cls(name, value)
        header_instance.as_unstructured = as_unstructured
        return header_instance


relay_header_factory = RelayHeaderRegistry()
relay_header_factory.registry["message-id"] = cast(
    type["_HeaderParser"], RelayMessageIDHeader
)
