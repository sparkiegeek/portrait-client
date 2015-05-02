#from portrait.tests.helpers import LandscapeTest
import unittest

from portrait.old.schema import (
    InvalidError, Constant, Bool, Int, Float, Bytes, Unicode, List, KeyDict,
    Dict, Tuple, Any, Message)


class DummySchema(object):
    def coerce(self, value):
        return "hello!"

class BasicTypesTest(unittest.TestCase):

    def test_any(self):
        schema = Any(Constant(None), Unicode())
        self.assertEqual(schema.coerce(None), None)
        self.assertEqual(schema.coerce("foo"), "foo")

    def test_any_bad(self):
        schema = Any(Constant(None), Unicode())
        self.assertRaises(InvalidError, schema.coerce, object())

    def test_constant(self):
        self.assertEqual(Constant("hello").coerce("hello"), "hello")

    def test_constant_arbitrary(self):
        obj = object()
        self.assertEqual(Constant(obj).coerce(obj), obj)

    def test_constant_bad(self):
        self.assertRaises(InvalidError, Constant("foo").coerce, object())

    def test_bool(self):
        self.assertEqual(Bool().coerce(True), True)
        self.assertEqual(Bool().coerce(False), False)

    def test_bool_bad(self):
        self.assertRaises(InvalidError, Bool().coerce, 1)

    def test_int(self):
        self.assertEqual(Int().coerce(3), 3)

    def test_int_accepts_long(self):
        self.assertEqual(Int().coerce(3), 3)

    def test_int_bad_str(self):
        self.assertRaises(InvalidError, Int().coerce, "3")

    def test_int_bad_float(self):
        self.assertRaises(InvalidError, Int().coerce, 3.0)

    def test_float(self):
        self.assertEqual(Float().coerce(3.3), 3.3)

    def test_float_accepts_int(self):
        self.assertEqual(Float().coerce(3), 3.0)

    def test_float_accepts_long(self):
        self.assertEqual(Float().coerce(3), 3.0)

    def test_float_bad_str(self):
        self.assertRaises(InvalidError, Float().coerce, "3.0")

    def test_string(self):
        self.assertEqual(Bytes().coerce("foo"), "foo")

    @unittest.skip
    def test_string_bad_unicode(self):
        self.assertRaises(InvalidError, Bytes().coerce, "foo")

    def test_string_bad_anything(self):
        self.assertRaises(InvalidError, Bytes().coerce, object())

    def test_unicode(self):
        self.assertEqual(Unicode().coerce("foo"), "foo")

    def test_unicode_bad_value(self):
        """Invalid values raise an errors."""
        self.assertRaises(InvalidError, Unicode().coerce, 32)

    def test_unicode_with_str(self):
        """Unicode accept plain strings and return a unicode."""
        self.assertEqual(Unicode().coerce("foo"), "foo")

    @unittest.skip
    def test_unicode_decodes(self):
        """Unicode should decode plain strings."""
        a = "\N{HIRAGANA LETTER A}"
        self.assertEqual(Unicode().coerce(a), a)
        letter = "\N{LATIN SMALL LETTER A WITH GRAVE}"
        self.assertEqual(
            Unicode(encoding="latin-1").coerce(letter.encode("latin-1")),
            letter)

    @unittest.skip
    def test_unicode_or_str_bad_encoding(self):
        """Decoding errors should be converted to InvalidErrors."""
        self.assertRaises(InvalidError, Unicode().coerce, "\xff")

    def test_list(self):
        self.assertEqual(List(Int()).coerce([1]), [1])

    def test_list_bad(self):
        self.assertRaises(InvalidError, List(Int()).coerce, 32)

    def test_list_inner_schema_coerces(self):
        self.assertEqual(List(DummySchema()).coerce([3]), ["hello!"])

    def test_list_bad_inner_schema(self):
        self.assertRaises(InvalidError, List(Int()).coerce, ["hello"])

    def test_list_multiple_items(self):
        a = "\N{HIRAGANA LETTER A}"
        b = "something"
        schema = List(Unicode())
        self.assertEqual(schema.coerce([a, b]), [a, b])

    def test_tuple(self):
        self.assertEqual(Tuple(Int()).coerce((1,)), (1,))

    def test_tuple_coerces(self):
        self.assertEqual(Tuple(Int(), DummySchema()).coerce((23, object())),
                         (23, "hello!"))

    def test_tuple_bad(self):
        self.assertRaises(InvalidError, Tuple().coerce, object())

    def test_tuple_inner_schema_bad(self):
        self.assertRaises(InvalidError, Tuple(Int()).coerce, (object(),))

    def test_tuple_must_have_all_items(self):
        self.assertRaises(InvalidError, Tuple(Int(), Int()).coerce, (1,))

    def test_tuple_must_have_no_more_items(self):
        self.assertRaises(InvalidError, Tuple(Int()).coerce, (1, 2))

    def test_key_dict(self):
        self.assertEqual(KeyDict({"foo": Int()}).coerce({"foo": 1}),
                         {"foo": 1})

    def test_key_dict_coerces(self):
        self.assertEqual(KeyDict({"foo": DummySchema()}).coerce({"foo": 3}),
                         {"foo": "hello!"})

    def test_key_dict_bad_inner_schema(self):
        self.assertRaises(InvalidError, KeyDict({"foo": Int()}).coerce,
                          {"foo": "hello"})

    def test_key_dict_unknown_key(self):
        self.assertRaises(InvalidError, KeyDict({}).coerce, {"foo": 1})

    def test_key_dict_bad(self):
        self.assertRaises(InvalidError, KeyDict({}).coerce, object())

    def test_key_dict_multiple_items(self):
        schema = KeyDict({"one": Int(), "two": List(Float())})
        input = {"one": 32, "two": [1.5, 2.3]}
        self.assertEqual(schema.coerce(input),
                         {"one": 32, "two": [1.5, 2.3]})

    def test_key_dict_arbitrary_keys(self):
        """
        KeyDict doesn't actually need to have strings as keys, just any
        object which hashes the same.
        """
        key = object()
        self.assertEqual(KeyDict({key: Int()}).coerce({key: 32}), {key: 32})

    def test_key_dict_must_have_all_keys(self):
        """
        dicts which are applied to a KeyDict must have all the keys
        specified in the KeyDict.
        """
        schema = KeyDict({"foo": Int()})
        self.assertRaises(InvalidError, schema.coerce, {})

    def test_key_dict_optional_keys(self):
        """KeyDict allows certain keys to be optional.
        """
        schema = KeyDict({"foo": Int(), "bar": Int()}, optional=["bar"])
        self.assertEqual(schema.coerce({"foo": 32}), {"foo": 32})

    def test_pass_optional_key(self):
        """Regression test. It should be possible to pass an optional key.
        """
        schema = KeyDict({"foo": Int()}, optional=["foo"])
        self.assertEqual(schema.coerce({"foo": 32}), {"foo": 32})

    def test_dict(self):
        self.assertEqual(Dict(Int(), Bytes()).coerce({32: "hello."}),
                         {32: "hello."})

    def test_dict_coerces(self):
        self.assertEqual(
            Dict(DummySchema(), DummySchema()).coerce({32: object()}),
            {"hello!": "hello!"})

    def test_dict_inner_bad(self):
        self.assertRaises(InvalidError, Dict(Int(), Int()).coerce, {"32": 32})

    def test_dict_wrong_type(self):
        self.assertRaises(InvalidError, Dict(Int(), Int()).coerce, 32)

    def test_message(self):
        """The L{Message} schema should be very similar to KeyDict."""
        schema = Message("foo", {"data": Int()})
        self.assertEqual(
            schema.coerce({"type": "foo", "data": 3}),
            {"type": "foo", "data": 3})

    def test_message_timestamp(self):
        """L{Message} schemas should accept C{timestamp} keys."""
        schema = Message("bar", {})
        self.assertEqual(
            schema.coerce({"type": "bar", "timestamp": 0.33}),
            {"type": "bar", "timestamp": 0.33})

    def test_message_api(self):
        """L{Message} schemas should accept C{api} keys."""
        schema = Message("baz", {})
        self.assertEqual(
            schema.coerce({"type": "baz", "api": "whatever"}),
            {"type": "baz", "api": "whatever"})

    def test_message_api_None(self):
        """L{Message} schemas should accept None for C{api}."""
        schema = Message("baz", {})
        self.assertEqual(
            schema.coerce({"type": "baz", "api": None}),
            {"type": "baz", "api": None})

    def test_message_optional(self):
        """The L{Message} schema should allow additional optional keys."""
        schema = Message("foo", {"data": Int()}, optional=["data"])
        self.assertEqual(schema.coerce({"type": "foo"}), {"type": "foo"})

    def test_message_type(self):
        """The C{type} should be introspectable on L{Message} objects."""
        schema = Message("foo", {})
        self.assertEqual(schema.type, "foo")

    def test_message_with_unknown_fields(self):
        """
        The L{Message} schema discards unknown fields when coercing values.
        """
        schema = Message("foo", {})
        self.assertEqual({"type": "foo"},
                         schema.coerce({"type": "foo", "crap": 123}))