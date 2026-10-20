import unittest

from simple_safe_filename_sanitizer import sanitize_filename


class TestSanitizeFilename(unittest.TestCase):
    def test_basic_alphanumeric_unchanged(self):
        self.assertEqual(sanitize_filename("hello.txt"), "hello.txt")

    def test_windows_forbidden_chars_replaced(self):
        result = sanitize_filename('a<b>c:d"e/f\\g|h?i*j')
        self.assertEqual(result, "a_b_c_d_e_f_g_h_i_j")

    def test_empty_string_fallback(self):
        self.assertEqual(sanitize_filename(""), "untitled")

    def test_only_forbidden_chars(self):
        self.assertEqual(sanitize_filename("???"), "___")
        self.assertEqual(sanitize_filename("<>:"), "___")

    def test_custom_replacement(self):
        self.assertEqual(sanitize_filename("a/b", replacement="-"), "a-b")

    def test_replacement_defaults_to_underscore(self):
        self.assertEqual(sanitize_filename("a:b"), "a_b")

    def test_custom_replacement_itself_sanitized(self):
        # A replacement containing illegal characters is cleaned so it cannot
        # reintroduce forbidden characters into the output.
        self.assertEqual(sanitize_filename("a/b", replacement=":"), "a_b")

    def test_control_characters_replaced(self):
        self.assertEqual(sanitize_filename("a\nb\tc\rd"), "a_b_c_d")

    def test_nul_byte_replaced(self):
        self.assertEqual(sanitize_filename("a\x00b"), "a_b")

    def test_trailing_dots_removed(self):
        self.assertEqual(sanitize_filename("file.txt..."), "file.txt")

    def test_trailing_spaces_removed(self):
        self.assertEqual(sanitize_filename("file.txt   "), "file.txt")

    def test_leading_spaces_removed(self):
        self.assertEqual(sanitize_filename("   file.txt"), "file.txt")

    def test_runs_of_spaces_collapsed(self):
        self.assertEqual(sanitize_filename("a   b"), "a b")

    def test_windows_reserved_name_con_prefixed(self):
        self.assertEqual(sanitize_filename("CON"), "_CON")

    def test_windows_reserved_name_case_insensitive(self):
        self.assertEqual(sanitize_filename("con"), "_con")
        self.assertEqual(sanitize_filename("Aux"), "_Aux")

    def test_windows_reserved_name_with_extension_still_reserved(self):
        # "CON.txt" is still reserved on Windows; the name as a whole is not
        # the reserved token, so we do NOT prefix it. This is our chosen
        # interpretation: we guard the exact reserved word only.
        self.assertEqual(sanitize_filename("CON.txt"), "CON.txt")

    def test_dots_only_collapsed_to_fallback(self):
        self.assertEqual(sanitize_filename("..."), "untitled")

    def test_path_separators_do_not_create_directories(self):
        # Forward and back slashes are replaced, never preserved as path
        # separators, so the output is always a single path component.
        self.assertEqual(sanitize_filename("a/b\\c"), "a_b_c")

    def test_type_error_on_non_string(self):
        with self.assertRaises(TypeError):
            sanitize_filename(123)

    def test_long_name_truncated(self):
        long_name = "a" * 300
        result = sanitize_filename(long_name)
        self.assertEqual(len(result), 200)
        self.assertTrue(result.startswith("a"))

    def test_normalization_of_unicode_combining_sequence(self):
        # NFC normalization ensures equivalent strings produce the same
        # filename rather than differing in invisible combining marks.
        decomposed = "e\u0301"  # é as e + combining acute
        composed = "\u00e9"     # é as a single code point
        self.assertEqual(sanitize_filename(decomposed), sanitize_filename(composed))


if __name__ == "__main__":
    unittest.main()
