# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Rules-related classes."""

from collections import namedtuple

from google.cloud.security.scanner.audit import errors as audit_errors


# pylint: disable=too-few-public-methods
class Rule(object):
    """Encapsulate Rule properties from the rule definition file.

    The reason this is not a named tuple is that it needs to be hashable.
    The ResourceRules class has a set of Rules.
    """

    def __init__(self, rule_name, rule_index, bindings, mode=None):
        """Initialize.

        Args:
            rule_name: The string name of the rule.
            rule_index: The rule's index in the rules file.
            bindings: The list of IamPolicyBindings for this rule.
            mode: The RulesMode for this rule.
        """
        self.rule_name = rule_name
        self.rule_index = rule_index
        self.bindings = bindings
        self.mode = RuleMode.verify(mode)

    def __eq__(self, other):
        """Test whether Rule equals other Rule."""
        if not isinstance(other, type(self)):
            return NotImplemented
        return (self.rule_name == other.rule_name and
                self.rule_index == other.rule_index and
                self.bindings == other.bindings and
                self.mode == other.mode)

    def __ne__(self, other):
        """Test whether Rule is not equal to another Rule."""
        return not self == other

    def __hash__(self):
        """Make a hash of the rule index.

        For now, this will suffice since the rule index is assigned
        automatically when the rules map is built, and the scanner
        only handles one rule file at a time. Later on, we'll need to
        revisit this hash method when we process multiple rule files.

        Returns:
            The hash of the rule index.
        """
        return hash(self.rule_index)

    def __repr__(self):
        """Returns the string representation of this Rule."""
        return 'Rule <{}, name={}, mode={}, bindings={}>'.format(
            self.rule_index, self.rule_name, self.mode, self.bindings)


class RuleAppliesTo(object):
    """What the rule applies to. (Default: SELF) """

    SELF = 'self'
    CHILDREN = 'children'
    SELF_AND_CHILDREN = 'self_and_children'
    apply_types = frozenset([SELF, CHILDREN, SELF_AND_CHILDREN])

    @classmethod
    def verify(cls, applies_to):
        """Verify whether the applies_to is valid."""
        if applies_to not in cls.apply_types:
            raise audit_errors.InvalidRulesSchemaError(
                'Invalid applies_to: {}'.format(applies_to))
        return applies_to


class RuleMode(object):
    """The rule mode."""

    WHITELIST = 'whitelist'
    BLACKLIST = 'blacklist'
    REQUIRED = 'required'

    modes = frozenset([WHITELIST, BLACKLIST, REQUIRED])

    @classmethod
    def verify(cls, mode):
        """Verify whether the mode is valid."""
        if mode not in cls.modes:
            raise audit_errors.InvalidRulesSchemaError(
                'Invalid rule mode: {}'.format(mode))
        return mode


# Rule violation.
# resource_type: string
# resource_id: string
# rule_name: string
# rule_index: int
# violation_type: VIOLATION_TYPE
# role: string
# members: tuple of IamPolicyBindings
RuleViolation = namedtuple('RuleViolation',
                           ['resource_type', 'resource_id', 'rule_name',
                            'rule_index', 'violation_type', 'role', 'members'])

# Rule violation types.
VIOLATION_TYPE = {
    'whitelist': 'ADDED',
    'blacklist': 'ADDED',
    'required': 'REMOVED',
    'UNSPECIFIED': 'UNSPECIFIED'
}
