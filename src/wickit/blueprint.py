"""blueprint - JSON Schema Validation.

Create and validate JSON schemas with detailed error messages.
Supports validation rules, required fields, and type checking.

Example:
    >>> from wickit import blueprint
    >>> schema = blueprint.make_schema({
    ...     "type": "object",
    ...     "properties": {
    ...         "name": {"type": "string"},
    ...         "age": {"type": "number"}
    ...     },
    ...     "required": ["name"]
    ... })
    >>> blueprint.validate(data, schema)

Classes:
    SchemaError: Validation error with details.
    FieldSchema: Individual field schema.
    Schema: JSON schema wrapper.

Functions:
    make_schema: Create schema from dictionary.
    validate: Validate data, raise on error.
    validate_required_fields: Check required fields.
    validate_json_file: Validate file.
    safe_validate: Validate, return result.

Pre-built Schemas (COMMON_SCHEMAS):
    USER_SCHEMA, SETTINGS_SCHEMA, DECK_SCHEMA, PROFILE_SCHEMA
"""

import json
from dataclasses import dataclass
from typing import Any, Optional


class SchemaError(Exception):
    """Raised when schema validation fails."""
    pass


@dataclass
class FieldSchema:
    """Schema for a single field."""
    type: str = "any"
    required: bool = False
    default: Any = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    choices: Optional[list] = None
    nested_schema: Optional[dict] = None


@dataclass
class Schema:
    """Complete schema definition."""
    fields: dict[str, FieldSchema]
    allow_extra: bool = False


def get_type(value: Any) -> str:
    """Get the type name of a value."""
    if isinstance(value, str):
        return "string"
    elif isinstance(value, bool):
        return "boolean"
    elif isinstance(value, int):
        return "integer"
    elif isinstance(value, float):
        return "number"
    elif isinstance(value, list):
        return "array"
    elif isinstance(value, dict):
        return "object"
    elif value is None:
        return "null"
    else:
        return "unknown"


def validate_type(value: Any, expected_type: str, field_name: str) -> None:
    """Validate that a value matches the expected type."""
    if expected_type == "any":
        return

    actual_type = get_type(value)

    if expected_type == "string" and actual_type != "string":
        raise SchemaError(f"{field_name}: expected string, got {actual_type}")
    elif expected_type == "boolean" and actual_type != "boolean":
        raise SchemaError(f"{field_name}: expected boolean, got {actual_type}")
    elif expected_type == "integer" and actual_type != "integer":
        raise SchemaError(f"{field_name}: expected integer, got {actual_type}")
    elif expected_type == "number" and actual_type not in ("integer", "number"):
        raise SchemaError(f"{field_name}: expected number, got {actual_type}")
    elif expected_type == "array" and actual_type != "array":
        raise SchemaError(f"{field_name}: expected array, got {actual_type}")
    elif expected_type == "object" and actual_type != "object":
        raise SchemaError(f"{field_name}: expected object, got {actual_type}")
    elif expected_type == "null" and actual_type != "null":
        raise SchemaError(f"{field_name}: expected null, got {actual_type}")


def validate_value(value: Any, schema: FieldSchema, field_name: str) -> None:
    """Validate a value against a field schema."""
    validate_type(value, schema.type, field_name)

    if schema.min_value is not None and isinstance(value, (int, float)):
        if value < schema.min_value:
            raise SchemaError(f"{field_name}: value {value} is below minimum {schema.min_value}")

    if schema.max_value is not None and isinstance(value, (int, float)):
        if value > schema.max_value:
            raise SchemaError(f"{field_name}: value {value} is above maximum {schema.max_value}")

    if schema.min_length is not None and isinstance(value, str):
        if len(value) < schema.min_length:
            raise SchemaError(f"{field_name}: string length {len(value)} is below minimum {schema.min_length}")

    if schema.max_length is not None and isinstance(value, str):
        if len(value) > schema.max_length:
            raise SchemaError(f"{field_name}: string length {len(value)} exceeds maximum {schema.max_length}")

    if schema.choices is not None and value not in schema.choices:
        raise SchemaError(f"{field_name}: value '{value}' not in allowed choices {schema.choices}")

    if schema.nested_schema is not None and isinstance(value, dict):
        nested_schema = Schema(
            fields={k: FieldSchema(**v) for k, v in schema.nested_schema.items()}
        )
        validate(value, nested_schema, field_name)


def validate(data: dict, schema: Schema, prefix: str = "") -> dict:
    """Validate data against a schema.

    Args:
        data: The data to validate
        schema: The schema to validate against
        prefix: Prefix for error messages

    Returns:
        Validated data with defaults applied

    Raises:
        SchemaError: If validation fails
    """
    if not isinstance(data, dict):
        raise SchemaError(f"{prefix}: expected object, got {get_type(data)}")

    validated = {}

    for field_name, field_schema in schema.fields.items():
        if field_name not in data:
            if field_schema.required:
                raise SchemaError(f"{prefix}.{field_name}: required field is missing")
            if field_schema.default is not None:
                validated[field_name] = field_schema.default
            continue

        value = data[field_name]
        full_name = f"{prefix}.{field_name}" if prefix else field_name

        try:
            if value is None and field_schema.type != "null":
                if field_schema.default is not None:
                    validated[field_name] = field_schema.default
                continue
            validate_value(value, field_schema, full_name)
            validated[field_name] = value
        except SchemaError as e:
            raise SchemaError(str(e))

    if not schema.allow_extra:
        extra_fields = set(data.keys()) - set(schema.fields.keys())
        if extra_fields:
            raise SchemaError(f"{prefix}: unexpected fields: {', '.join(extra_fields)}")

    return validated


def validate_required_fields(data: dict, required_fields: list, prefix: str = "") -> None:
    """Validate that required fields are present.

    Args:
        data: The data to validate
        required_fields: List of required field names
        prefix: Prefix for error messages

    Raises:
        SchemaError: If any required field is missing
    """
    missing = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing.append(field)

    if missing:
        full_prefix = f"{prefix}." if prefix else ""
        raise SchemaError(f"{full_prefix}missing required fields: {', '.join(missing)}")


def validate_json_file(file_path: str, schema: Schema) -> dict:
    """Validate a JSON file against a schema.

    Args:
        file_path: Path to the JSON file
        schema: The schema to validate against

    Returns:
        Validated data

    Raises:
        SchemaError: If validation fails
        IOError: If file cannot be read
    """
    with open(file_path) as f:
        data = json.load(f)

    return validate(data, schema, file_path)


def make_schema(fields: dict, allow_extra: bool = False) -> Schema:
    """Create a Schema from a simpler dict format.

    Args:
        fields: Dict of field_name -> field config
        allow_extra: Whether to allow extra fields

    Returns:
        Schema object
    """
    parsed_fields = {}
    for name, config in fields.items():
        if isinstance(config, dict):
            parsed_fields[name] = FieldSchema(**config)
        else:
            parsed_fields[name] = FieldSchema(type=str(config), required=True)

    return Schema(fields=parsed_fields, allow_extra=allow_extra)


@dataclass
class ValidationResult:
    """Result of a validation check."""
    valid: bool
    data: Optional[dict]
    errors: list


def safe_validate(data: dict, schema: Schema) -> ValidationResult:
    """Validate data without raising exceptions.

    Returns:
        ValidationResult with valid flag, data, and errors
    """
    try:
        validated = validate(data, schema)
        return ValidationResult(valid=True, data=validated, errors=[])
    except SchemaError as e:
        return ValidationResult(valid=False, data=None, errors=[str(e)])


COMMON_SCHEMAS = {
    "base_json": make_schema({
        "version": {"type": "string", "required": True},
        "personal": {"type": "object", "required": True},
        "experience": {"type": "array", "required": True},
        "education": {"type": "array", "required": True},
        "skills": {"type": "array", "required": True},
    }),

    "session": make_schema({
        "id": {"type": "string", "required": True},
        "date": {"type": "string", "required": True},
        "questions": {"type": "array", "required": True, "nested_schema": {
            "question": {"type": "string", "required": True},
            "answer": {"type": "string", "required": True},
            "correct": {"type": "boolean", "required": True},
        }},
    }),
}
