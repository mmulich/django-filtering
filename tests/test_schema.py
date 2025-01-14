import json

from jsonschema.protocols import Validator

from django_filtering import filters
from django_filtering.schema import FilteringOptionsSchema, JSONSchema

from tests.lab_app.models import Participant
from tests.lab_app.filters import ParticipantFilterSet


class TestJsonSchema:
    def test_generation_of_schema(self):
        """
        Using the ParticipantScopedFilterSet with filters set in the Meta class,
        expect only those specified fields and lookups to be valid for use.
        """
        valid_filters = {
            "age": ["gte", "lte"],
            "sex": ["icontains"],
        }

        class ScopedFilterSet(filters.FilterSet):
            age = filters.Filter(
                filters.InputLookup('gte', label="greater than or equal to"),
                filters.InputLookup('lte', label="less than or equal to"),
                default_lookup="gte",
                label="Age",
            )
            sex = filters.Filter(
                filters.InputLookup('icontains', label='contains'),
                default_lookup='icontains',
                label="Sex",
            )

            class Meta:
                model = Participant

        filterset = ScopedFilterSet()
        json_schema = JSONSchema(filterset)
        schema = json_schema.schema

        # Check valid json-schema
        # Raises `jsonschema.exceptions.SchemaError` if there is an issue.
        Validator.check_schema(json_schema.schema)

        # Verify expected `$defs`, no more or less definitions
        expected_defs = ['and-or-op', 'not-op', 'filters'] + [f"{n}-filter" for n in valid_filters]
        assert sorted(schema['$defs'].keys()) == sorted(expected_defs)

        # Verify filters defined in the `#/$defs/filters` container
        expected = [{'$ref': f"#/$defs/{n}-filter"} for n in valid_filters]
        assert schema['$defs']['filters']['anyOf'] == expected

        # Look for the particular filters
        expected_age_filter = {
            'type': 'array',
            'prefixItems': [
                {'const': 'age'},
                {
                    'type': 'object',
                    'properties': {
                        'lookup': {'enum': valid_filters['age']},
                        'value': {'type': 'string'}
                    }
                }
            ]
        }
        assert schema['$defs']['age-filter'] == expected_age_filter
        expected_sex_filter = {
            'type': 'array',
            'prefixItems': [
                {'const': 'sex'},
                {
                    'type': 'object',
                    'properties': {
                        'lookup': {'enum': valid_filters['sex']},
                        'value': {'type': 'string'}
                    }
                }
            ]
        }
        assert schema['$defs']['sex-filter'] == expected_sex_filter

    def test_to_json(self):
        filterset = ParticipantFilterSet()
        json_schema = JSONSchema(filterset)

        assert json.dumps(json_schema.schema) == str(json_schema)
        assert json.loads(str(json_schema))


class TestFilteringOptionsSchema:
    def test_generation_of_schema(self):
        valid_filters = {
            "age": {
                "gte": {"type": "input", "label": "greater than or equal to"},
                "lte": {"type": "input", "label": "less than or equal to"},
            },
            "sex": {"exact": {"type": "input", "label": "equals"}},
        }

        class ScopedFilterSet(filters.FilterSet):
            age = filters.Filter(
                filters.InputLookup('gte', label="greater than or equal to"),
                filters.InputLookup('lte', label="less than or equal to"),
                default_lookup="gte",
                label="Age",
            )
            sex = filters.Filter(
                filters.InputLookup('exact', label='equals'),
                default_lookup='exact',
                label="Sex",
            )

            class Meta:
                model = Participant

        filterset = ScopedFilterSet()
        schema = FilteringOptionsSchema(filterset)

        # Check for operators
        expected = ['and', 'or', 'not']
        assert sorted(schema.schema['operators'].keys()) == sorted(expected)

        # Check for the valid FilterSet
        assert sorted(schema.schema['filters'].keys()) == sorted(valid_filters.keys())

        # Check for filters
        expected = {'default_lookup': list(valid_filters['age'].keys())[0], 'lookups': valid_filters['age'], 'label': 'Age'}
        assert schema.schema['filters']['age'] == expected
        expected = {'default_lookup': list(valid_filters['sex'].keys())[0], 'lookups': valid_filters['sex'], 'label': 'Sex'}
        assert schema.schema['filters']['sex'] == expected

    def test_to_json(self):
        filterset = ParticipantFilterSet()
        schema = FilteringOptionsSchema(filterset)

        assert json.dumps(schema.schema) == str(schema)
        assert json.loads(str(schema))
