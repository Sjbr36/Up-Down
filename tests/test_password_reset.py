import unittest

from database import parse_password_reset_params


class ParsePasswordResetParamsTests(unittest.TestCase):
    def test_extracts_recovery_data_from_query_params(self) -> None:
        params = {"type": "recovery", "token_hash": "abc123"}
        self.assertEqual(
            parse_password_reset_params(params),
            {"token_hash": "abc123", "type": "recovery"},
        )

    def test_defaults_to_recovery_when_access_token_is_present(self) -> None:
        params = {"access_token": "xyz789"}
        self.assertEqual(
            parse_password_reset_params(params),
            {"token_hash": "xyz789", "type": "recovery"},
        )


if __name__ == "__main__":
    unittest.main()
